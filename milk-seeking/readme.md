# Milk Truck Dataset Generator, Training Scripts

Here's more info: https://racenis.github.io/synthetic-data/milk-seeking/

# Building

The easiest way to build the template would be to run CMake. Make sure that you
have CMake and a C++20 compiler installed. Then run the `cmake` command to
generate the build files for your toolchain.

The CMake script will automatically download and compile all of the
dependencies. If you are using Windows, you won't need anything extra, but on
Linux you might need to install additional dependencies (for OpenGL and X11
development).
 
For Debian/Ubuntu systems you can try running
```
sudo apt-get install libmesa-dev
sudo apt-get install xorg-dev
```
For Fedora based systems try running
```
sudo dnf install mesa-libGL-devel libX11-devel libXcursor-devel libXi-devel libXinerama-devel libXrandr-devel
```