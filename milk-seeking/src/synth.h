#ifndef SYNTH_H
#define SYNTH_H

#include "scenario.h"

#include <framework/uid.h>

using namespace tram;

class SynthScenario : public Scenario {
public:
	SynthScenario(name_t worldcell, bool auto_capture);
	
	virtual void Setup() override;
	virtual void Teardown() override;
	virtual void Update() override;
private:
	name_t worldcell;
	bool auto_capture;
};

#endif // SYNTH_H