import datetime
import qrcode
from PIL import Image

point_of_initiation = '12'
proxy_type = '0'
proxy_value = '+6512345678'
editable = '1'
amount  = '0.01'
expiry = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y%m%d') # one day later, YYYMMDD
bill_number = 'it works xD'

'''
Function to translate QR information dictionary payload to string of characters 
Works for any layers of nested objects (for this case we only have one nested layer ID 26)
'''
def get_info_string(info):
    final_string = '' # Empty string to store the generated output
    for key, value in info.items(): # Loop through the outer dictionary
        if type(value) == dict: # If there is a nested dictionary
            temp_string_length, temp_string = get_info_string(value) #call this function recusively to get the nested info
            # Adds the ID, length and value of the nested object
            final_string += key 
            final_string += temp_string_length
            final_string += temp_string
        else: # Normal value, adds the 3 fields: ID, length, value
            final_string += key
            final_string += str(len(value)).zfill(2)
            final_string += value
    return str(len(final_string)).zfill(2), final_string # Returns the length of the current string and its value

def generatePayNowQR(point_of_initiation,
                    proxy_type,
                    proxy_value,
                    editable,
                    amount,
                    expiry,
                    bill_number
                    ):
       '''
       Nested dictionary that follows the structure of the data object
       dictionary key = data object id, 
       dictionary value = data object value
       Application can also insert new key-value pairs corrosponding to its ID-value in whichever nested layer
       as long as the first and last root ID are 00 and 63 respectively. Order doesnt matter for the rest.
       '''
       info = {"00":"01",
              "01":str(point_of_initiation),
              "26":{"00":"SG.PAYNOW",
                     "01":str(proxy_type),
                     "02":str(proxy_value),
                     "03":str(editable),
                     "04":str(expiry)
                     } ,
              "52":"0000",
              "53":"702",
              "54":str(amount),
              "58":"SG",
              "59":"NA",
              "60":"Singapore",
              "62":{"01":str(bill_number)}
              }
       payload = get_info_string(info)[1] # gets the final string, length is not needed
       payload += '6304' # append ID 63 and length 4 (generated result will always be of length 4)
       crc_value = crc16_ccitt(payload) # calculate CRC checksum
       crc_value = ('{:04X}'.format(crc_value)) #convert into 4 digit uppercase hex
       payload += crc_value # add the CRC checksum result

       # Creating an instance of qrcode
       qr = qrcode.QRCode(
              version = 1, # the size of QR code matrix.
              box_size = 5, # how many pixels is each box of the QR code
              border = 4, # how thick is the border
              error_correction = qrcode.constants.ERROR_CORRECT_H,) # able to damage/cover the QR Code up to a certain percentage. H - 30% 
       qr.add_data(payload)
       qr.make(fit=True) #QR code to fit the entire dimension even when the input data could fit into fewer boxes
       img = qr.make_image(fill_color=(144,19,123), back_color='white') #PayNow purple colour
       
       # Adding PayNow logo to the center
       logo = Image.open('./paynow_logo.png')
       # adjust logo image size 
       basewidth = 85 # adjust this value for logo size
       wpercent = (basewidth/float(logo.size[0]))
       hsize = int((float(logo.size[1])*float(wpercent)))
       logo = logo.resize((basewidth, hsize), Image.Resampling.LANCZOS)
       # set position of logo and paste it 
       pos = ((img.size[0] - logo.size[0]) // 2,
              (img.size[1] - logo.size[1]) // 2)
       img.paste(logo, pos)
       
       img.save('generated_qr.png')
       
def crc16_ccitt(data): 
    crc = 0xFFFF # initial value
    msb = crc >> 8
    lsb = crc & 255
    for c in data:
        x = ord(c) ^ msb
        x ^= (x >> 4)
        msb = (lsb ^ (x >> 3) ^ (x << 4)) & 255
        lsb = (x ^ (x << 5)) & 255
    return (msb << 8) + lsb

generatePayNowQR(point_of_initiation,
              proxy_type,
              proxy_value,
              editable,
              amount,
              expiry,
              bill_number
              )
'''
Other working CRC-16 (CCITT) algorithms:
------------------------------------------------------------------------------
External library dependant

import pycrc.algorithms
crc = pycrc.algorithms.Crc(width = 16, poly = 0x1021,
          reflect_in = False, xor_in = 0xffff,
          reflect_out = False, xor_out = 0x0000)

# calculate the CRC, using the bit-by-bit-fast algorithm.
crc_value = crc.bit_by_bit_fast(payload)
crc_value = ('{:04X}'.format(crc_value))

------------------------------------------------------------------------------
Implemented with a precomputed lookup table

def crc16(data: bytes):
table = [ 
       0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50A5, 0x60C6, 0x70E7, 0x8108, 0x9129, 0xA14A, 0xB16B, 0xC18C, 0xD1AD, 0xE1CE, 0xF1EF,
       0x1231, 0x0210, 0x3273, 0x2252, 0x52B5, 0x4294, 0x72F7, 0x62D6, 0x9339, 0x8318, 0xB37B, 0xA35A, 0xD3BD, 0xC39C, 0xF3FF, 0xE3DE,
       0x2462, 0x3443, 0x0420, 0x1401, 0x64E6, 0x74C7, 0x44A4, 0x5485, 0xA56A, 0xB54B, 0x8528, 0x9509, 0xE5EE, 0xF5CF, 0xC5AC, 0xD58D,
       0x3653, 0x2672, 0x1611, 0x0630, 0x76D7, 0x66F6, 0x5695, 0x46B4, 0xB75B, 0xA77A, 0x9719, 0x8738, 0xF7DF, 0xE7FE, 0xD79D, 0xC7BC,
       0x48C4, 0x58E5, 0x6886, 0x78A7, 0x0840, 0x1861, 0x2802, 0x3823, 0xC9CC, 0xD9ED, 0xE98E, 0xF9AF, 0x8948, 0x9969, 0xA90A, 0xB92B,
       0x5AF5, 0x4AD4, 0x7AB7, 0x6A96, 0x1A71, 0x0A50, 0x3A33, 0x2A12, 0xDBFD, 0xCBDC, 0xFBBF, 0xEB9E, 0x9B79, 0x8B58, 0xBB3B, 0xAB1A,
       0x6CA6, 0x7C87, 0x4CE4, 0x5CC5, 0x2C22, 0x3C03, 0x0C60, 0x1C41, 0xEDAE, 0xFD8F, 0xCDEC, 0xDDCD, 0xAD2A, 0xBD0B, 0x8D68, 0x9D49,
       0x7E97, 0x6EB6, 0x5ED5, 0x4EF4, 0x3E13, 0x2E32, 0x1E51, 0x0E70, 0xFF9F, 0xEFBE, 0xDFDD, 0xCFFC, 0xBF1B, 0xAF3A, 0x9F59, 0x8F78,
       0x9188, 0x81A9, 0xB1CA, 0xA1EB, 0xD10C, 0xC12D, 0xF14E, 0xE16F, 0x1080, 0x00A1, 0x30C2, 0x20E3, 0x5004, 0x4025, 0x7046, 0x6067,
       0x83B9, 0x9398, 0xA3FB, 0xB3DA, 0xC33D, 0xD31C, 0xE37F, 0xF35E, 0x02B1, 0x1290, 0x22F3, 0x32D2, 0x4235, 0x5214, 0x6277, 0x7256,
       0xB5EA, 0xA5CB, 0x95A8, 0x8589, 0xF56E, 0xE54F, 0xD52C, 0xC50D, 0x34E2, 0x24C3, 0x14A0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
       0xA7DB, 0xB7FA, 0x8799, 0x97B8, 0xE75F, 0xF77E, 0xC71D, 0xD73C, 0x26D3, 0x36F2, 0x0691, 0x16B0, 0x6657, 0x7676, 0x4615, 0x5634,
       0xD94C, 0xC96D, 0xF90E, 0xE92F, 0x99C8, 0x89E9, 0xB98A, 0xA9AB, 0x5844, 0x4865, 0x7806, 0x6827, 0x18C0, 0x08E1, 0x3882, 0x28A3,
       0xCB7D, 0xDB5C, 0xEB3F, 0xFB1E, 0x8BF9, 0x9BD8, 0xABBB, 0xBB9A, 0x4A75, 0x5A54, 0x6A37, 0x7A16, 0x0AF1, 0x1AD0, 0x2AB3, 0x3A92,
       0xFD2E, 0xED0F, 0xDD6C, 0xCD4D, 0xBDAA, 0xAD8B, 0x9DE8, 0x8DC9, 0x7C26, 0x6C07, 0x5C64, 0x4C45, 0x3CA2, 0x2C83, 0x1CE0, 0x0CC1,
       0xEF1F, 0xFF3E, 0xCF5D, 0xDF7C, 0xAF9B, 0xBFBA, 0x8FD9, 0x9FF8, 0x6E17, 0x7E36, 0x4E55, 0x5E74, 0x2E93, 0x3EB2, 0x0ED1, 0x1EF0
]

crc = 0xFFFF
for byte in data:
       crc = (crc << 8) ^ table[(crc >> 8) ^ byte]
       crc &= 0xFFFF         # important, crc must stay 16bits all the way through
return str(hex(crc)).upper().replace('0X','')
crc_value = crc16(str.encode(payload))
'''