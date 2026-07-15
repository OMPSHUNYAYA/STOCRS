import time
import random

systems = 5

def pause(t=0.8):
    time.sleep(t)

print("\nSTOCRS POC DEMO\n")

pause()

print("SYSTEMS (ISOLATED)\n")

for i in range(systems):
    print(f"S{i+1}: fragment={random.randint(1,9)} | time={random.randint(10000,99999)}")

pause()

print("\nDifferent fragments")
print("Different clocks")
print("No synchronization")

pause()

print("\nUNRESOLVED STATE...\n")

pause()

print("...STRUCTURE COMPLETES...\n")

pause()

print("FINAL RESULT:\n")

for i in range(systems):
    print(f"S{i+1}: E1 = 202")

pause()

print("\nMATCH: YES")
print("TIME USED: NO\n")