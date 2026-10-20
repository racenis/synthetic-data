default: project

src_main.o: ./src/main.cpp
	g++ -c -g -O0 -Wno-narrowing -std=c++20 -I./src -I../../tram-sdk/libraries -I../../tram-sdk/src -I../../tram-sdk/libraries/glfw -I../../tram-sdk/libraries/glad -I../../tram-sdk/libraries/bullet -I../../tram-sdk/libraries/lua ./src/main.cpp -o src_main.o

src_segmentable.o: ./src/segmentable.cpp
	g++ -c -g -O0 -Wno-narrowing -std=c++20 -I./src -I../../tram-sdk/libraries -I../../tram-sdk/src -I../../tram-sdk/libraries/glfw -I../../tram-sdk/libraries/glad -I../../tram-sdk/libraries/bullet -I../../tram-sdk/libraries/lua ./src/segmentable.cpp -o src_segmentable.o
	
src_scenario.o: ./src/scenario.cpp
	g++ -c -g -O0 -Wno-narrowing -std=c++20 -I./src -I../../tram-sdk/libraries -I../../tram-sdk/src -I../../tram-sdk/libraries/glfw -I../../tram-sdk/libraries/glad -I../../tram-sdk/libraries/bullet -I../../tram-sdk/libraries/lua ./src/scenario.cpp -o src_scenario.o

src_synth.o: ./src/synth.cpp
	g++ -c -g -O0 -Wno-narrowing -std=c++20 -I./src -I../../tram-sdk/libraries -I../../tram-sdk/src -I../../tram-sdk/libraries/glfw -I../../tram-sdk/libraries/glad -I../../tram-sdk/libraries/bullet -I../../tram-sdk/libraries/lua ./src/synth.cpp -o src_synth.o

src_drone.o: ./src/drone.cpp
	g++ -c -g -O0 -Wno-narrowing -std=c++20 -I./src -I../../tram-sdk/libraries -I../../tram-sdk/src -I../../tram-sdk/libraries/glfw -I../../tram-sdk/libraries/glad -I../../tram-sdk/libraries/bullet -I../../tram-sdk/libraries/lua ./src/drone.cpp -o src_drone.o

clean:
	del src_main.o
	del src_segmentable.o
	del src_scenario.o
	del src_synth.o
	del src_drone.o

project: src_main.o src_segmentable.o src_scenario.o src_synth.o src_drone.o 
	g++ -o template -L../../tram-sdk/ -static src_main.o src_segmentable.o src_synth.o src_drone.o src_scenario.o -ltramsdk  -lglfw3 -lgdi32  -L../../tram-sdk/libraries/binaries/win64/ -lOpenAL32    -lBulletSoftBody -lBulletDynamics -lBulletCollision -lLinearMath       -llua 