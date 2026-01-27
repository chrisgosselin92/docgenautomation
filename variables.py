from db import set_client_variable

def bulk_add_variables(client_ids, var_names, default_value=None):
    """Add/update multiple variables for multiple clients."""
    for client_id in client_ids:
        for var_name in var_names:
            set_client_variable(client_id, var_name, default_value)
