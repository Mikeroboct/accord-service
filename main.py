import base64

import accord_tools
from accord_tools.accord_service import AccordService

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    asg_service = AccordService()
    with open('Customer-Sample.pdf', 'rb') as file:
        byte_array = file.read()
        base64_bytes = base64.b64encode(byte_array)
        base64_string = base64_bytes.decode('utf-8')

    asg_service.extract_accord_data(base64_string)

