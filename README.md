# PyEncoder
a module for testing out various entropy encoding algorithms. Algorithms that re currently supported:
1. Arithmetic Coding (Adaptive & Static)
1. Huffman Coding (Adaptive & Static)
1. Run Length Coding (not 100% supported)

# Usage 
The functions defined below are the consistent for all modules, all that's needed is to just import and use it. 

### Adaptive Coding
data and the encoded bits can be passed into the algorithm incrementally, whenever necessary.

#### Encoding
```python
    encoder = AdaptiveEncoder()

    encoded_data = ""
    for sym in StringData:
        encoded_data += encoder.encode(sym)
    encoded_data += encoder.flush()

```

#### Decoding
```python
    decoder = algorithm.main.AdaptiveDecoder()
    chunk_size = 64

    decoded_data = ""
    for i in range(0, len(encoded_data), chunk_size):
        decoded_data += decoder.decode(encoded_data[i : i + 8])
    decoded_data += decoder.flush()

```

### Static Coding
data and encoded bits must be passed into the algorithm in bulk, aka all at once.

#### Encoding
```python
    codebook, encoded_data = encode(StringData)
```

#### Decoding
```
    decoded_data = decoder(codebook, encoded_data)
```

### IO 
write to / reading from file

#### Encoding

```python

    with open("data.txt", "r") as data_file, open("encoded_file.dat", mode="wb") as encoded_file:
        dump(txt_file, encoded_file)
```

#### Decoding

```python
    with open("encoded_file.dat", "rb") as encoded_file, open("decoded_file.txt", mode="w") as decoded_file:
        load(encoded_file, decoded_file)
```

# Settings
specific settings, like endianess, permitted symbols and etc can be tweaked to one's liking using the `Setting` object, by simply assigning the attribute.
```
from pyencoder import Setting

Setting.ENDIAN = "little"
```