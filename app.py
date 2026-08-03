import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import ctypes
import os

# --- 1. Load the C Library ---
lib_path = os.path.join(os.path.dirname(__file__), 'libcubiomes.so')
cubiomes = ctypes.CDLL(lib_path)

# --- 2. Define C Structures in Python ---
class Generator(ctypes.Structure):
    # 100KB buffer to prevent memory corruption in 1.18+ generation
    _fields_ = [("data", ctypes.c_byte * 100000)] 

cubiomes.setupGenerator.argtypes = [ctypes.POINTER(Generator), ctypes.c_int, ctypes.c_uint]
cubiomes.setupGenerator.restype = None

cubiomes.applySeed.argtypes = [ctypes.POINTER(Generator), ctypes.c_int, ctypes.c_uint64]
cubiomes.applySeed.restype = None

cubiomes.getBiomeAt.argtypes = [ctypes.POINTER(Generator), ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
cubiomes.getBiomeAt.restype = ctypes.c_int

# MC 1.21 constant for Bedrock 1.26 parity
MC_1_21 = 21 
DIM_OVERWORLD = 0

# --- 3. The Streamlit UI ---
# Makes it look good on mobile
st.set_page_config(page_title="Seed Mapper", layout="centered") 

st.title("🗺️ Pocket Edition Seed Mapper")
st.write("Enter your Bedrock seed to instantly map the biomes around spawn.")

# User input - changed to text_input to handle 64-bit Bedrock seeds safely
seed_input_str = st.text_input("Minecraft Seed", value="12345")

if st.button("Generate Map", type="primary"):
    with st.spinner("Calculating biomes..."):
        # Safely convert the string to an integer
        try:
            seed_val = int(seed_input_str)
        except ValueError:
            st.error("Please enter a valid number.")
            st.stop()
            
        # Initialize generator
        g = Generator()
        cubiomes.setupGenerator(ctypes.byref(g), MC_1_21, 0)
        
        # Apply the converted seed
        cubiomes.applySeed(ctypes.byref(g), DIM_OVERWORLD, ctypes.c_uint64(seed_val))        
        # Grid setup (200x200 blocks)
        radius = 100 
        biome_grid = np.zeros((radius*2, radius*2))
        
        # Generation loop (stepping by 4 for speed)
        for x in range(-radius, radius, 4):
            for z in range(-radius, radius, 4):
                biome_id = cubiomes.getBiomeAt(ctypes.byref(g), 1, x, 64, z)
                biome_grid[x+radius:x+radius+4, z+radius:z+radius+4] = biome_id

        # Render the map
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.imshow(biome_grid, cmap='tab20', interpolation='nearest') 
        ax.axis('off')
        
        st.pyplot(fig)
