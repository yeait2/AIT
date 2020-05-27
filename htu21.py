import smbus

import time



bus = smbus.SMBus(2)



def crc8atm(data) :

    data =data << 8

    length = len(bin(data)[2:]) 

    for i in range(length):

        if int(bin(data)[2:3], 2) == 1:

            nokori = bin(data)[11:] 

            sentou = (int(bin(data)[2:11], 2)) ^ (int('100110001', 2))  # crc-8=x8+x5+x4+1=100110001

            data = int((str(bin(sentou)[2:11]) + str(nokori)), 2)

            data = int(bin(data), 2)

        if len(str(bin(data)[2:])) < 9:

            return (hex(data))





while True:

	time.sleep(1)

	

	#温度表示(block)

	

	t1 = bus.read_i2c_block_data(0x40, 0xe3, 3)

	#print('t1', t1)



	t1_msb = t1[0]

	t1_lsb = t1[1]

	t1_data = t1[0]*256 + t1[1]



	crc8_t1 = crc8atm(t1_data)

	#print(crc8_t1)

	#print(hex(t1[2]))



	if int(crc8_t1,16) == t1[2]:

		#print('pec ok!')



		Temp1 = (t1_data / 2**16) * 175.72 - 46.85

		print(round(Temp1,2), 'degC')



	else:

		print('pec is incorrect!!!!!')

		break





	#湿度表示(block)

	

	rh1 = bus.read_i2c_block_data(0x40, 0xe5, 3)

	#print('rh1', rh1)



	rh1_msb = rh1[0]

	rh1_lsb = rh1[1]

	rh1_data = rh1[0]*256 + rh1[1]



	crc8_rh1 = crc8atm(rh1_data)

	#print(crc8_rh1)

	#print(hex(rh1[2]))



	if int(crc8_rh1,16) == rh1[2]:

		#print('pec ok!')

		RH1 = (rh1_data / 2**16) * 125 - 6

		print(round(RH1,2), '%RH')



	else:

		print('pec is incorrect!!!!!')

		break
