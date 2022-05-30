from time import sleep
import smbus


class i2c_device:
    def __init__(self, addr, port=1):
        self.addr = addr
        self.bus = smbus.SMBus(port)

# Write a single command
    def write_cmd(self, cmd):
        self.bus.write_byte(self.addr, cmd)
        sleep(0.0001)

# Write a command and argument
    def write_cmd_arg(self, cmd, data):
        self.bus.write_byte_data(self.addr, cmd, data)
        sleep(0.0001)

# Write a block of data
    def write_block_data(self, cmd, data):
        self.bus.write_block_data(self.addr, cmd, data)
        sleep(0.0001)

# Read a single byte
    def read(self):
        return self.bus.read_byte(self.addr)

# Read
    def read_data(self, cmd):
        return self.bus.read_byte_data(self.addr, cmd)

# Read a block of data
    def read_block_data(self, cmd):
        return self.bus.read_block_data(self.addr, cmd)


En = 0b00000100  # Enable bit
Rw = 0b00000010  # Read/Write bit
Rs = 0b00000001  # Register select bit


class lcd4bit:
    # initializes objects and lcd
    def __init__(self):
        self.lcd_device = i2c_device(0x39)  # via i2cdetect
        self.send_instruction(0x03)
        self.send_instruction(0x03)
        self.send_instruction(0x03)
        self.send_instruction(0x02)

        self.send_instruction(0x28)  # Function set 4 BIT
        # send_instruction(0x28)  # Function set 4 BIT
        self.send_instruction(0x0F)  # Display on of 0xf 0b00001111
        self.send_instruction(0x01)
        sleep(0.2)

    def lcd_strobe(self, data):
        self.lcd_device.write_cmd(data | En)
        sleep(.0005)
        self.lcd_device.write_cmd(((data & ~En)))
        sleep(.0001)

    def set_data_bits(self, data):
        self.lcd_device.write_cmd(data)
        self.lcd_strobe(data)

    # write a command to lcd
    def send_instruction(self, cmd, mode=0x0):
        self.set_data_bits(mode | (cmd & 0xF0))
        self.set_data_bits(mode | ((cmd << 4) & 0xF0))

    def send_character(self, charvalue, mode=1):
        self.set_data_bits(mode | (charvalue & 0xF0))
        self.set_data_bits(mode | ((charvalue << 4) & 0xF0))

    def write_message(self, message):
        aantalchars = 1
        for char in message:
            aantalchars += 1
            self.send_instruction(ord(char), Rs)
            if aantalchars == 17:
                self.send_instruction(0x80 | 0x40)
                aantalchars += 1

    def clear_lcd(self):
        self.send_instruction(0x01)

    def second_line(self):
        self.send_instruction(0x80 | 0x40)

    def first_line(self):
        self.send_instruction(0x80)


mylcd = lcd4bit()
mylcd.write_message("")
mylcd.first_line()
