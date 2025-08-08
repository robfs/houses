import sqlite3
from collections.abc import Collection

import orjson as json


class HouseQuery:
    def _column_string(
        self, paths: Collection[tuple[str, str]], root: str = "data"
    ) -> str:
        columns = []
        for path, name in paths:
            if "." in path:
                clean_path = path.strip(".")
                column = f"json_extract({root}, '$.{clean_path}') as {name}"
            else:
                column = f"{path} as {name}"
            columns.append(column)

        return ", ".join(columns)

    def _add_filters(self, query: str, **kwargs) -> str:
        if not kwargs:
            return query
        filters = [f"{key} = '{value}'" for key, value in kwargs.items()]
        filter_str = " and ".join(filters)
        return query + f" where {filter_str}"

    def atomic_query(self, paths: Collection[tuple[str, str]], **kwargs) -> str:
        column_str = self._column_string(paths)
        query = f"select {column_str} from houses"
        return self._add_filters(query, **kwargs)

    def array_query(
        self, array_path: str, paths: Collection[tuple[str, str]], **kwargs
    ) -> str:
        column_str = self._column_string(paths, "value")
        query = (
            f"select {column_str} from houses, json_each(houses.data, '$.{array_path}')"
        )
        return self._add_filters(query, **kwargs)


class JSONStore:
    def __init__(self, db_path) -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            """
            create table if not exists houses (
                property_number text primary key,
                status text,
                data JSON
            )
            """
        )

    def set(self, property_number, status, data):
        self.conn.execute(
            "insert or replace into houses (property_number, status, data) values (?, ?, ?)",
            (property_number, status, json.dumps(data)),
        )
        self.conn.commit()

    def get(self, key):
        cursor = self.conn.execute(
            "select data from houses where property_number = ?", (key,)
        )
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None

    def delete(self, property_number):
        query = "delete from houses where property_number = ?"
        self.conn.execute(query, property_number)
        self.conn.commit()

    def update_status(self, property_number, status):
        query = "update houses set status = ? where property_number = ?"
        self.conn.execute(query, (status, property_number))
        self.conn.commit()

    def get_main_table_data(self, status: str):
        query = HouseQuery().atomic_query(
            [
                ("property_number", "property_number"),
                ("propertyData.address.displayAddress", "description"),
            ],
            status=status,
        )
        cursor = self.conn.execute(query)
        return cursor.fetchall()

    def get_image_urls(self, property_number: str) -> list[str]:
        query = HouseQuery().array_query(
            "propertyData.images", [(".url", "url")], property_number=property_number
        )
        cursor = self.conn.execute(query)
        data = cursor.fetchall()
        return [row["url"] for row in data]
