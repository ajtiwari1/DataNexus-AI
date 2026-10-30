ALLOWED_SQL_TOOLS = {
    "list_tables",
    "describe_table",
    "run_readonly_query",
}


def filter_allowed_tools(tools):
    allowed_tools = [
        tool
        for tool in tools
        if tool.name in ALLOWED_SQL_TOOLS
    ]

    rejected_tools = [
        tool.name
        for tool in tools
        if tool.name not in ALLOWED_SQL_TOOLS
    ]

    return allowed_tools, rejected_tools