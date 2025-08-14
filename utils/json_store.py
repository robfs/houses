from collections.abc import Collection


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


#     return [row["url"] for row in data]
