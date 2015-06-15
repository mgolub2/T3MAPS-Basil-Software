from lt3maps import *
import sys

driver = T3MAPSDriver("lt3maps.yaml")
driver.set_global_register(column_address=int(sys.argv[1]),config_mode=0,hitor_strobe=0,hit_strobe=0,inject_strobe=0,TDAC_strobes=0b10100,enable_strobes=1)
#driver.set_global_register(column_address=int(sys.argv[1]))
driver.write_global_reg()
output = driver.run()

print (output)
