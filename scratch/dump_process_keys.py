import ctypes
import re
import os
import psutil

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
MEM_COMMIT = 0x1000
PAGE_READWRITE = 0x04
PAGE_READONLY = 0x02

my_pid = os.getpid()
flask_pid = None

for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        cmd = proc.info['cmdline']
        if cmd and any('app.py' in part for part in cmd) and proc.info['pid'] != my_pid:
            flask_pid = proc.info['pid']
            print(f"Found Flask process: PID={flask_pid}, cmdline={cmd}")
            break
    except Exception:
        pass

if not flask_pid:
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == 'python.exe' and proc.info['pid'] != my_pid:
            flask_pid = proc.info['pid']
            print(f"Fallback to Python process: PID={flask_pid}")
            break

if not flask_pid:
    print("No target Python process found.")
    exit(1)

kernel32 = ctypes.windll.kernel32
OpenProcess = kernel32.OpenProcess
ReadProcessMemory = kernel32.ReadProcessMemory
VirtualQueryEx = kernel32.VirtualQueryEx
CloseHandle = kernel32.CloseHandle

class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", ctypes.c_uint32),
        ("RegionSize", ctypes.c_size_t),
        ("State", ctypes.c_uint32),
        ("Protect", ctypes.c_uint32),
        ("Type", ctypes.c_uint32),
    ]

process_handle = OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, flask_pid)
if not process_handle:
    print("Failed to open process handle.")
    exit(1)

# Set up type signatures for 64-bit Windows compatibility
VirtualQueryEx.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(MEMORY_BASIC_INFORMATION), ctypes.c_size_t]
VirtualQueryEx.restype = ctypes.c_size_t

ReadProcessMemory.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
ReadProcessMemory.restype = ctypes.c_bool

address = 0
mbi = MEMORY_BASIC_INFORMATION()
keys_found = set()
key_pat = re.compile(rb'(AQ\.[a-zA-Z0-9_-]{30,80}|AIzaSy[a-zA-Z0-9_-]{30,50})')

while VirtualQueryEx(process_handle, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi)) > 0:
    if mbi.State == MEM_COMMIT and (mbi.Protect & (PAGE_READWRITE | PAGE_READONLY)):
        buffer = ctypes.create_string_buffer(mbi.RegionSize)
        bytes_read = ctypes.c_size_t(0)
        if ReadProcessMemory(process_handle, mbi.BaseAddress, buffer, mbi.RegionSize, ctypes.byref(bytes_read)):
            chunk = buffer.raw[:bytes_read.value]
            for match in key_pat.findall(chunk):
                try:
                    key_str = match.decode('utf-8')
                    keys_found.add(key_str)
                except Exception:
                    pass
    address += mbi.RegionSize

CloseHandle(process_handle)

print(f"\nScan completed. Found {len(keys_found)} unique key patterns:")
for k in sorted(keys_found):
    print(k)
