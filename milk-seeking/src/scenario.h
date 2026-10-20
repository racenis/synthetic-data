#ifndef SCENARIO_H
#define SCENARIO_H

class Scenario {
public:
	virtual void Setup() = 0;
	virtual void Teardown() = 0;
	virtual void Update() = 0;
};

#endif // SCENARIO_H