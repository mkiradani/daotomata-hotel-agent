"""Debug function tool structure."""

from app.agents.pms_tools import check_real_room_availability

def inspect_function_tool():
    """Inspect the function tool structure."""
    
    print("Function tool inspection:")
    print(f"Type: {type(check_real_room_availability)}")
    print(f"Dir: {[attr for attr in dir(check_real_room_availability) if not attr.startswith('_')]}")
    
    # Check if it has common attributes
    attributes_to_check = ['func', 'function', 'callable', '__call__', '__wrapped__']
    
    for attr in attributes_to_check:
        if hasattr(check_real_room_availability, attr):
            print(f"Has {attr}: {getattr(check_real_room_availability, attr)}")
    
    print(f"\nIs callable: {callable(check_real_room_availability)}")

if __name__ == "__main__":
    inspect_function_tool()