# py-rigol
Python interface to Rigol Programmable Power Supplies and E-Loads

### Example Usage:
```
from dl_3000 import DL3000

# if you know the resource_id you want to connect to (such as DL3A192600119), you can do:
with DL3000.from_resource_id("your_resource_id_here") as eLoad:
    # Use the eLoad...

# If you don't know the resource_id and want to connect to any DL3000 series available, you can do:
with DL3000.auto_connect() as eLoad:
    # Use the eLoad...


