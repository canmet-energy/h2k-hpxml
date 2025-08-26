

def get_val(obj, path):
    """Get a value from a nested dictionary using a comma-separated path.

    Args:
        obj: The dictionary to search
        path: Comma-separated path to the value (e.g., "key1,key2,key3")

    Returns:
        The value at the specified path, or the original object if not found
    """
    for key in path.split(","):
        # returns itself if nothing found so we can use paths containing higher level info
        obj = obj.get(key, obj)

    return obj
