import streamlit as st
import numpy as np
import plotly.express as px
import ctypes
import os

# --- 1. Load the C Library ---
lib_path = os.path.join(os.path.dirname(__file__), 'libcubiomes.so')
cubiomes = ctypes.CDLL(lib_path)

# --- 2. Define C Structures & Constants ---
class Generator(ctypes.Structure):
    _fields_ = [("data", ctypes.c_byte * 100000)] 

cubiomes.setupGenerator.argtypes = [ctypes.POINTER(Generator), ctypes.c_int, ctypes.c_uint]
cubiomes.setupGenerator.restype = None
cubiomes.applySeed.argtypes = [ctypes.POINTER(Generator), ctypes.c_int, ctypes.c_uint64]
cubiomes.applySeed.restype = None
cubiomes.getBiomeAt.argtypes = [ctypes.POINTER(Generator), ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
cubiomes.getBiomeAt.restype = ctypes.c_int

MC_1_21 = 21 
DIM_OVERWORLD = 0

# --- 3. Biome Color & Name Dictionary ---
# Format: Biome ID: ([R, G, B], "Biome Name")
# Note: I have included the most common biomes here. You can easily add more IDs later.
BIOME_MAP = {
    0: ([0, 0, 112], "Ocean"),
    1: ([141, 179, 96], "Plains"),
    2: ([250, 148, 24], "Desert"),
    3: ([96, 96, 96], "Windswept Hills"),
    4: ([5, 102, 33], "Forest"),
    5: ([11, 102, 89], "Taiga"),
    6: ([7, 249, 178], "Swamp"),
    7: ([0, 0, 255], "River"),
    12: ([255, 255, 255], "Snowy Tundra"),
    14: ([255, 0, 255], "Mushroom Fields"),
    16: ([217, 69, 21], "Beach"),
    21: ([36, 140, 49], "Jungle"),
    37: ([217, 69, 21], "Badlands"),
    39: ([150, 150, 150], "Stony Peaks"),
    44: ([0, 0, 80], "Deep Ocean")
}
DEFAULT_BIOME = ([128, 128, 128], "Unknown Biome") # Gray for unmapped IDs

# --- 4. The Streamlit UI ---
st.set_page_config(page_title="Seed Mapper", layout="wide") 

st.title("🗺️ Interactive Seed Mapper")
st.write("Enter your seed to generate an interactive, draggable map. Hover over blocks to see the biome name.")

# Use columns for a cleaner layout
col1, col2 = st.columns([1, 3])

with col1:
    seed_input_str = st.text_input("Minecraft Seed", value="4456948524525964067")
    radius = st.slider("Map Radius (Blocks)", min_value=100, max_value=500, value=200, step=100)
    generate = st.button("Generate Map", type="primary")

with col2:
    if generate:
        with st.spinner("Simulating terrain generation..."):
            try:
                seed_val = int(seed_input_str)
            except ValueError:
                st.error("Please enter a valid number.")
                st.stop()
                
            g = Generator()
            cubiomes.setupGenerator(ctypes.byref(g), MC_1_21, 0)
            cubiomes.applySeed(ctypes.byref(g), DIM_OVERWORLD, ctypes.c_uint64(seed_val))
            
            # Create grids for Colors (RGB) and Text (Hover labels)
            grid_size = int((radius * 2) / 4)
            color_grid = np.zeros((grid_size, grid_size, 3), dtype=np.uint8)
            name_grid = np.empty((grid_size, grid_size), dtype=object)
            
            # Step by 4 for performance
            for i, x in enumerate(range(-radius, radius, 4)):
                for j, z in enumerate(range(-radius, radius, 4)):
                    biome_id = cubiomes.getBiomeAt(ctypes.byref(g), 1, x, 64, z)
                    
                    # Look up the color and name, or use default gray if not in our dictionary
                    biome_data = BIOME_MAP.get(biome_id, DEFAULT_BIOME)
                    
                    color_grid[j, i] = biome_data[0] # Note: j, i aligns the X/Z axes correctly
                    name_grid[j, i] = f"{biome_data[1]} (ID: {biome_id})<br>X: {x} | Z: {z}"

            # Render interactive map with Plotly
            fig = px.imshow(color_grid)
            fig.update_traces(
                customdata=name_grid,
                hovertemplate="%{customdata}<extra></extra>"
            )
            fig.update_layout(
                xaxis_title="West -> East (X)",
                yaxis_title="North -> South (Z)",
                margin=dict(l=0, r=0, t=0, b=0),
                dragmode="pan" # Enables dragging
            )
            
            # Display interactive chart
            st.plotly_chart(fig, use_container_width=True)
