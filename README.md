# Particle Generator

![particle-thumb](https://github.com/user-attachments/assets/42445ce0-b0a9-47d2-a2cd-6e6c6566c193)

**Author:** The French Monkey (TFMSTYLE)  
**Version:** 1.0.0  

---

## Overview

The Particle Generator creates large-scale, procedural particle distributions using geometry nodes instancing.  
It includes multiple spatial patterns such as galaxies, rings, spheres, and clouds, each with tunable parameters for density, noise, and structure.  
Each generated system instantiates thousands of lightweight mesh instances with random scaling and automatic material assignment.  
Perfect for visual effects, sci-fi scenes, or abstract simulations.

---

## Parameters

### Live Update
When enabled, automatically rebuilds the particle system as parameters are adjusted.  
Useful for interactive exploration, but may reduce performance at high particle counts.

---

### Pattern
Determines the spatial arrangement of generated particles.  
Available options include:

- **Galaxy:** Spiral galaxy-like distribution with multiple arms and controlled spin.  
- **Sphere:** Spherical shell or volume with optional thickness and surface noise.  
- **Ring:** Circular or toroidal band of particles with vertical thickness.  
- **Cloud:** Volumetric cluster with randomized spread and noise falloff.

---

### Particle Count
Defines the total number of generated points in the distribution.  
Higher values create denser particle fields.

---

### Radius
Controls the overall size of the particle formation.  
Larger values expand the particle field proportionally in all directions.

---

### Thickness
Adjusts the vertical or radial depth of the formation, depending on the selected pattern.  
Higher values produce more volumetric or layered structures.

---

### Noise
Adds random positional variation to the particle placement.  
Increases irregularity and natural appearance of the distribution.

---

### Seed
Sets the randomization seed used in particle placement.  
Changing this creates new configurations with identical settings.

---

### Arms
For **Galaxy** patterns, defines the number of spiral arms.  
Higher values produce more complex galactic structures.

---

### Spin
For **Galaxy** patterns, controls the spiral tightness.  
Higher values increase the rotational sweep of the arms.

---

### Scale Min
Defines the minimum random scaling factor applied to each particle instance.  
Used to introduce size variation across particles.

---

### Scale Max
Defines the maximum random scaling factor applied to each particle instance.  
Combined with **Scale Min**, this sets the range of size variability.

---

## Operators

### Generate Particles
Creates a new particle distribution based on the selected pattern and parameters,  
or regenerates the currently selected one if it was produced by the Particle Generator.  
Automatically applies instancing, scaling variation, and a default particle material.

---

## Usage Notes

- Choose a **Pattern** (Galaxy, Sphere, Ring, or Cloud) to define the base distribution.  
- Adjust **Particle Count**, **Radius**, and **Noise** to shape the spread and density.  
- Modify **Scale Min** and **Scale Max** to introduce natural size variation.  
- Enable **Live Update** for iterative design when exploring parameters.  
- The add-on uses a Geometry Nodes modifier to instance mesh particles efficiently.  
- A default material (`ParticleMaterial`) is automatically created and assigned.  
- Ideal for procedural scattering, cosmic visuals, or abstract compositions.
