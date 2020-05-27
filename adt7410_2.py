import smbus
import time

i2c = smbus.SMBus(2)
address = 0x48

index = 0
while index < 10:
    block = i2c.read_i2c_block_data(address, 0x00, 12)
    temp = (block[0] << 8 | block[1]) >> 3
    
    if(temp >= 4096):
        temp -= 8192
    print("%.1f" % (temp / 16.0))
    time.sleep(1)
    index += 1
