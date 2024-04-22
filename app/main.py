import re
import sys
from dataclasses import dataclass

import logging
logging.basicConfig(
    level = 'DEBUG',
    )

command = sys.argv[2]
database_file_path = sys.argv[1]

IS_FIRST_BIT_ZERO_MASKED = 0x80  # 0b10000000
LAST_SEVEN_BITS_MASK = 0x7F  # 0b01111111

def starts_with_zero(byte):
    return (byte & IS_FIRST_BIT_ZERO_MASKED) == 0

def usable_value(usable_size, byte):
    return byte if usable_size == 8 else byte & LAST_SEVEN_BITS_MASK

class Stream:
    def __init__(self, database_file):
        self.database_file = database_file

    def read_usable_bytes(self):
        usable_bytes = []
        for i in range(8):
            byte = int.from_bytes(self.database_file.read(1), byteorder="big")
            usable_bytes.append(byte)
            if starts_with_zero(byte):
                break
        return usable_bytes

    def read_varint(self):
        value = 0
        binary = 0b010
        for _ in range(9):
            byte = int.from_bytes(self.database_file.read(1), byteorder="big")
            # logging.debug('%d: this is byte: %r', _, bin(byte))
            value = value << 7 | (byte & LAST_SEVEN_BITS_MASK)
            if byte & IS_FIRST_BIT_ZERO_MASKED == 0:
                break
        return value

    def parse_column(self, serial_type):
        if serial_type >= 13 and serial_type % 2 == 1:
            n_bytes = (serial_type - 13) // 2
            return self.database_file.read(n_bytes).decode()
        if serial_type >= 12 and serial_type % 2 == 0:
            n_bytes = (serial_type - 12) // 2
            return self.database_file.read(n_bytes).decode()
        if serial_type == 1:
            return int.from_bytes(self.database_file.read(1), byteorder="big")
        if serial_type == 0:
            return None
        if serial_type == 7 or serial_type == 6:
            return int.from_bytes(self.database_file.read(8), byteorder="big")
        raise Exception(f"Unknown Serial Type {serial_type}")

    def parse_record(self, column_count):
        serial_types = [self.read_varint() for _ in range(column_count)]
        return [self.parse_column(serial_type) for serial_type in serial_types]

    def table_schema(self):
        # Skipping the main header
        self.database_file.seek(100)
        # After the header, we will have page_header which is from 8 byte to 12 byte
        page_type = int.from_bytes(self.database_file.read(1), byteorder="big")
        free_block = int.from_bytes(self.database_file.read(2), byteorder="big")
        cell_count = int.from_bytes(self.database_file.read(2), byteorder="big")
        content_start = int.from_bytes(self.database_file.read(2), byteorder="big")
        fragmented_free_bytes = int.from_bytes(self.database_file.read(1), byteorder="big")
        # After the main header, and page header is the cell pointers to table schema all in page 1
        # note that in another page, we only have page header and then data
        cell_pointers = [
            int.from_bytes(self.database_file.read(2), byteorder="big")
            for _ in range(cell_count)
        ]

        tables = []
        for cell_pointer in cell_pointers:
            # This is table header
            self.database_file.seek(cell_pointer)
            payload_size = self.read_varint()
            row_id = self.read_varint()
            _bytes_in_header = self.read_varint()
            cols = self.parse_record(5)
            sqlite_schema = {
                "type": cols[0],
                "name": cols[1],
                "tbl_name": cols[2],
                "rootpage": cols[3],
                "sql": cols[4],
            }
            tables.append(sqlite_schema)
        return tables


def command_dbinfo(database_file_path):
    with open(database_file_path, "rb") as database_file:
        print("Logs from your program will appear here!")
        # Uncomment this to pass the first stage
        database_file.seek(16)  # Skip the first 16 bytes of the header
        page_size = int.from_bytes(database_file.read(2), byteorder="big")
        database_file.seek(103)
        cell_count = int.from_bytes(database_file.read(2), byteorder="big")
        print(f"database page size: {page_size}")

        print(f"number of tables: {cell_count}")


def command_tables(database_file_path):
    with open(database_file_path, "rb") as database_file:
        stream = Stream(database_file)
        print(" ".join([
            x["name"]
            for x in stream.table_schema()
            if x["name"] != "sqlite_sequence"
        ]))

def command_select(database_file_path):
    # parsing the command
    # stream = Stream(database_file_path)
    has_count = "count(" in command.lower()
    select_cols = command.lower().split("from")[0].replace("select ", "").split(",")
    select_cols = [col.strip() for col in select_cols if len(col.strip()) > 0]
    table_name = (
        command.lower().split("from")[1].strip().split(" ")[0].replace("\\n", "")

    )
    with open(database_file_path, "rb") as database_file:
        stream = Stream(database_file)
        database_file.seek(16)
        page_size = int.from_bytes(database_file.read(2), byteorder="big")
        tables = stream.table_schema() # get the table schema informations type, name, tblname, rootpage, sql
        
        # Get the table that has name match with slq query
        table_info_all = [table for table in tables if table["name"] == table_name] 
        # get the first table that match
        table_info = table_info_all[0] if len(table_info_all) > 0 else exit()
        
        # we did know the order of colums, so this one show us the order
        schema_cols = (
            table_info["sql"]
            .replace("\n", "")
            .replace("\t", "")
            .split("(")[1]
            .split(")")[0]
            .split(",")
        )
        
        schema_cols = [col.strip().split(" ")[0].strip() for  col in schema_cols] 
        if table_info is None:
            print("Table Not F ound")
        # Now go the the real table
        table_cell_offset = (table_info["rootpage"] - 1) * page_size
        database_file.seek(table_cell_offset)
        
        # table header
        page_type = int.from_bytes(database_file.read(1), byteorder="big")
        free_block = int.from_bytes(database_file.read(2), byteorder="big")
        cell_count = int.from_bytes(database_file.read(2), byteorder="big")
        content_start = int.from_bytes(database_file.read(2), byteorder="big")
        fragmented_free_bytes = int.from_bytes(database_file.read(1), byteorder="big")
        if has_count:
            print(cell_count)
            exit()
            
        cell_pointers = [
            table_cell_offset + int.from_bytes(database_file.read(2), byteorder="big")
            for _ in range(cell_count)
        ]
        
        if "where" in command.lower():
            ccolumn, cvalue = [
                col.strip() 
                for col in command.lower().split("where")[1].split("=")
            ]
        rows = []
        
        for cell_pointer in cell_pointers:
            database_file.seek(cell_pointer)
            # row  headers
            payload_size = stream.read_varint()
            row_id = stream.read_varint()
            _bytes_in_header = stream.read_varint()
            
            cols = stream.parse_record(len(schema_cols))
            output = []
            show_row = not "where" in command.lower()
            for select_col in select_cols:
                try:
                    col_index = schema_cols.index(select_col)
                    value = cols[col_index].lower()
                    if "where" in command.lower():
                        if ccolumn == select_col and cvalue.replace("\'", "") == value:
                            show_row = True
                    output.append(cols[col_index])
                except:
                    print(f"Error: in prepare, no such column: {select_col}")
                    exit()
            if show_row:
                print("|".join(output)) 
    

if command == ".dbinfo":
    command_dbinfo(database_file_path)
elif command == ".tables":
    command_tables(database_file_path)
elif "select" in command.lower():
    command_select(database_file_path)
else:
    print(f"Invalid command: {command}")
    sys.exit(1)