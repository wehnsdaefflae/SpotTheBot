# Example how to call it with some added styling
# Also limit browsing files to .hex only (You can use anything: png, jpg, pdf etc.
from nicegui.events import UploadEventArguments

from src.components.file_picker import FilePicker


# Just an example of function that is called when file is removed
def reset_file_picker():
        print("Reset")
        # For example you can set props to some button to be disabled
        # new_fw_update_button.props("disable")
def show_file(file: UploadEventArguments):
        print("Here is your file")
        # You can parse your file here
        # Example for parsing a hex file
        spooled_temp_file = file.content
        print(f"New file uploaded: {file.name}")
        try:
            # Move the file cursor to the beginning
            spooled_temp_file.seek(0)
            byte_content = spooled_temp_file.read()
            byte_list = byte_content.split(b"\r\n")[:-1]
            print(f"Byte list: {byte_list}")
            # Do something with the file
        except Exception as e:
            print(f"Error: {e}")
        finally:
            # Close the file
            spooled_temp_file.close()

# Here you can add some styling to your file picker
value_input_style = "border rounded-lg focus:ring-blue-500 focus:border-blue-500 w-full bg-gray-50 border-gray-500 text-white"
# In this example I restricted file picker to only pick .hex files
uploader_element = FilePicker(on_pick=show_file,on_delete=reset_file_picker ,label="Browse File (.hex only)", accept_types=[".hex"]).classes(value_input_style+ "basis-1/2").props("dense clearable")