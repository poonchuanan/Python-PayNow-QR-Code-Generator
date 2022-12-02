# Python PayNow QR Code Generator 
Took quite a while to figure out the implementation due to lack of documentation online, so here's a consolidated version for myself to refer to in case I forget next time and hope it helps anyone thats interested as well.

The code is written with the goal for users to send $ to their friends easily for one of my apps. Modify the fields to suit your own needs.

## Introduction
PayNow QR is one of the many QR codes payment systems available in Singapore, developed by the Association of Banks in Singapore. Major banks such as DBS/POSB, OCBC, UOB supports it 
([Full list here](https://www.abs.org.sg/consumer-banking/pay-now) )

Other types of QR codes include those from other organisations, such as GrabPay, FavePay, Alipay, WeChat Pay or whatever nonsense. To prevent stalls from having to display 1001 QR codes, SGQR was launched to have a standardardised QR code format for all payment providers, essentially condensing all QR codes into one. The SGQR specifications are then based on guidelines issued by EMVCo.
**Specifications TLDR: PayNow ⊂ SGQR ⊂ EMVCo**

## Understanding the format
Scanning a PayNow QR (with any normal QR code scanner will give a string of characters).
> Example: **00**<u>02</u>01**01**<u>02</u>11**26**<u>43</u>0009SG.PAYNOW010120210T04SS0129D030110502QS**51**<u>81</u>0007SG.SGQR011221073031741D020701.00010306600316040201050327906040000070820210730**52**<u>04</u>0000**53**<u>03</u>702**58**<u>02</u>SG**59**<u>25</u>LOVING HEART MULTI-SERVIC**60**<u>09</u>Singapore**63**<u>04</u>A177

There are some details that are pretty obvious, like the receipent name. From here, all we need to do is to refer to the datasheets and reverse engineer the result to figure out the meaning of different fields.

Each data object is made up of 3 different fields:
1. **ID** (00-99)
2. <u>Length of value</u> (01-99)
3. Value (any characters)

From the example above, we can make sense of the string "**00**<u>02</u>01" as the first ID field starting at '00' having a value length of '02' containing the value '01'.

There can be nested data objects (value field is another data object, something like JSON). ID '26' has an example of nested data object.
> **00**<u>09</u>SG.PAYNOW**01**<u>01</u>2**02**<u>10</u>T04SS0129D**03**<u>01</u>1**05**<u>02</u>QS

## Important Fields for PayNow 
These are for the root fields aka the outer data objects (not nested).

| ID | Name | Purpose |
| ------ | ------ | ------ |
| 00 | Payload Format Indicator | Defines the version used (version 1) ∴ Fixed at "**00**<u>02</u>01"<br> **<u>First object</u>** under the root. |
| 01 | Point of Initiation Method | Static (same QR Code is shown for more than one transaction)- '11' <br> Dynamic (new QR Code is shown for each transaction)- '12' |
| 26 | Merchant Account Information | 02-25 is reserved (Table 4.3 of EMVCo pdf). <br> 26-50 is used for payment systems registered with SGQR, ID **26** in particular is usually used for PayNow. Other merchants information will take the subsequent IDs in order of registration. <br><br> PayNow payload (nested):<br> "**00**" - Reverse Domain Name. Fixed at “**00**<u>09</u>SG.PAYNOW” <br> "**01**" - Proxy Type. '0' for mobile number, '2' for UEN. <br> "**02**" - Proxy Value. Mobile/UEN number. <br> <i> <li>Mobile: <'+' International Dialling Code> followed by <up to 15-digit Mobile Number>. SG is '+65' </li><li> UEN: 9 or 10 (without suffix) OR 12 or 13 (with suffix) characters. </i></li> "**03**" - Editable. '0' for amount cannot be edited, '1' otherwise. <br> "**04**" - Expiry date (Optional). YYYYMMDD <br> "**05**" - Transaction Reference (Optional) - For record tracking, can be any characters. _Removed in PayNow v1.2. Use ID **62** -> Nested ID **01** Bill Number instead._|
| 51 | SGQR ID | Not mandatory for generating PayNow QR. <br> Used to identify each SGQR label (version, date of creation, physical location etc) |
| 52 | Merchant Category Code | 4-digits code to classify businesses (ISO 18245). <br> '0000' if not applicable. |
| 53 | Transaction Currency  | 3-digits currency code (ISO 4217). <br> '702' for SGD. |
| 54 | Transaction Amount | Self-explanatory. (ISO 4217) Up to 2dp. |
| 55 | Tip or Convenience Indicator | Optional, not really important. <br>  '01' - user input manually <br> '02' - include fixed fee <br> '03' - include percentage fee |
| 56 | Value of Convenience Fee Fixed  | Only exists if ID **55** is '02'. (ISO 4217) Up to 2dp. |
| 57 | Value of Convenience Fee Percentage  | Only exists if ID **55** is '03'. From 00.01-99.99|
| 58 | Country Code | 'SG' duhh |
| 59 | Merchant Name | Store Name. Dafault to 'NA'. |
| 60 | Merchant City | 'Singapore' duhhh |
| 61 | Postal Code | Optional |
| 62 | Additional Data Field Template | Transaction Reference. Optional.<br> "**01**" - Bill number (up to 25 characters) <br> "**02-99**" not in use for PayNow|
| 64 | Merchant Information Language Template | Merchant information in an alternate language. <br>Not important. |
| 65-79 | RFU for EMVCo | Data objects for EMVCo. <br> Not important. |
| 80-99 | Unreserved templates | Self-explanatory. <br> Not important. |
| 63 | CRC | Checksum calculated according to (ISO/IEC 13239). <br> **<u>Last object</u>** under the root. |

## CRC explanation
>4.7.3.1 The checksum shall be calculated according to [ISO/IEC 13239] using the polynomial 
'1021' (hex) and initial value 'FFFF' (hex). The data over which the checksum is 
calculated shall cover all data objects, including their ID, Length and Value, to be 
included in the QR Code, in their respective order, as well as the ID and Length of 
the CRC itself (but excluding its Value).
>
>4.7.3.2 Following the calculation of the checksum, the resulting 2-byte hexadecimal value 
shall be encoded as a 4-character Alphanumeric Special value by converting each 
nibble to the corresponding Alphanumeric Special character. A nibble with hex 
value ‘0’ is converted to “0” (= hex value ‘30’), a nibble with hex value ‘1’ is 
converted to “1” (= hex value ‘31’) and so on. Hex values ‘A’ to ‘F’ must be 
converted to uppercase characters “A” to “F” (= hex values ‘41’ to ‘46’).
Example: a CRC with a two-byte hexadecimal value of '007B' is converted to 
“007B” and included in the QR Code as "6304007B".

ISO 13239 (section 4.2.5.2) uses the polynomial  x<sup>16</sup> + x<sup>12</sup> + x<sup>5</sup> + 1 for its 16-bit frame checking sequence, which is the widely used CRC-CCITT. Converting the polynomial to binary, we get `1 0001 0000 0010 0001`(16th, 12th, 5th and 0th bit position). By right the polynomial value is 0x11021, but the most significant bit does not fit in 16 bits and it is usually dropped, resulting in 0x1021.

**Specifications of CRC-16-CCITT**:
- Width = 16 bits
- Truncated polynomial = 0x1021
- Initial value = 0xFFFF
- Input data is NOT reflected
- Output CRC is NOT reflected
- No XOR is performed on the output CRC

The result of the CRC will produce a 2-byte hexadecimal value (16 bits). Then, convert each nibble (4 bits) to its corresponding uppercase hex value 0-F, resulting in a 4-character hex value.
>61828 -> 1111 0001 1000 0100 -> F184

Therefore, all we need to do is to run the algorithm with the information string with the relevant fields populated (including '**63**<u>04</u>' at the end) to get the checksum and append it back to the original string to complete the information string.


## Reference
### Code
- https://gist.github.com/chengkiang/7e1c4899768245570cc49c7d23bc394c
- https://github.com/mindmedia/paynow.py
### CRC
- https://gist.github.com/oysstu/68072c44c02879a2abf94ef350d1c7c6
- https://stackoverflow.com/questions/25239423/crc-ccitt-16-bit-python-manual-calculation
- https://srecord.sourceforge.net/crc16-ccitt.html
### Others
- https://github.com/zionsg/sgqr-parser

