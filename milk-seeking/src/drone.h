#ifndef DRONE_H
#define DRONE_H

#include "scenario.h"

#include <framework/uid.h>
#include <framework/math.h>

#include <vector>

using namespace tram;

enum class DroneControl {
	THRUST,
	PITCH,
	ROLL,
};

struct Box {
	int x, y, w, h;
	float conf;
};

class DroneScenario : public Scenario {
public:
	DroneScenario(name_t worldcell, bool autopilot);
	
	void ApplyControl(DroneControl control, float amount);
	quat GetRotation();
	void DrawBoxes();
	
	virtual void Setup() override;
	virtual void Teardown() override;
	virtual void Update() override;
private:
	name_t worldcell;
	bool autopilot;
	
	vec3 position = {0.0f, 5.0f, 0.0f};
	vec3 velocity = {0.0f, 0.0f, -0.05f};
	float pitch = 0.0f, roll = 0.0f, yaw = 0.0f;
	
	std::vector<Box> boxes;
};

#endif // DRONE_H