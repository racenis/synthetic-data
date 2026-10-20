#include "synth.h"

#include "segmentable.h"

#include <framework/worldcell.h>
#include <framework/ui.h>

#include <platform/image.h>
#include <platform/api.h>

#include <render/render.h>
#include <render/scene.h>
#include <render/api.h>

#include <random>

const int NUMBER_OF_SEGMENTABLE = 17;

SynthScenario::SynthScenario(name_t worldcell, bool auto_capture) : worldcell(worldcell), auto_capture(auto_capture) {
	
}

static void reset_scene(name_t worldcell, bool single, bool as_segment) {
	WorldCell::Find(worldcell)->Unload();
	
	if (single) {
		Segmentable::SetLoadableIndex(-1);
	} else if (!as_segment) {
		static std::random_device rd;
		static std::mt19937 gen(rd());
		static std::uniform_int_distribution<int> dist(0, NUMBER_OF_SEGMENTABLE);
		Segmentable::SetLoadableIndex(dist(gen));
	}
	
	Segmentable::SetSegmentMode(as_segment);
	
	WorldCell::Find(worldcell)->Load();
	
	as_segment = !as_segment;
}

static void save_image(bool as_segment) {
	static int number = false;

	auto screen_width = UI::GetScreenWidth();
	auto screen_height = UI::GetScreenHeight();
	char* buffer = (char*)malloc(screen_width * screen_height * 3);
	
	char file_name[200];
	if (as_segment) {
		snprintf(file_name, 200, "%i-segment.png", number);
		number++;
	} else {
		snprintf(file_name, 200, "%i-image.png", number);
	}
	
	Render::API::GetScreen(buffer, screen_width, screen_height);
	Platform::SaveImageToDisk(file_name, screen_width, screen_height, buffer);
	
	free(buffer);	
}

static void setup_lighting() {
	auto dusk_sun = 0.4f * Render::COLOR_WHITE + 0.2f * Render::COLOR_YELLOW;
	auto dusk_amb = 0.1f * Render::COLOR_WHITE + 0.1f * Render::COLOR_CYAN;
	
	auto overcast_sun = 0.6f * Render::COLOR_WHITE + 0.2f * Render::COLOR_YELLOW;
	auto overcast_amb = 0.1f * Render::COLOR_WHITE + 0.1f * Render::COLOR_CYAN;
	
	auto daytime_sun = 0.9f * Render::COLOR_WHITE + 0.2f * Render::COLOR_RED;
	auto daytime_amb = 0.1f * Render::COLOR_WHITE + 0.1f * Render::COLOR_CYAN;
	
	static std::random_device rd;
    static std::mt19937 gen(rd());
    static std::uniform_real_distribution<float> dist(0.0f, 1.0f);

	auto perturb1 = vec3{dist(gen), dist(gen), dist(gen)} * 0.2f - 0.1f;
	auto perturb2 = vec3{dist(gen), dist(gen), dist(gen)} * 0.2f - 0.1f;
	
    float mixtype = dist(gen);
	if (mixtype < 0.33f) {
		Render::API::SetScreenClear(perturb1 + glm::mix(dusk_sun, overcast_sun, dist(gen)), true);
		Render::SetSunColor(perturb1 + glm::mix(dusk_sun, overcast_sun, dist(gen)));
		Render::SetAmbientColor(perturb2 + glm::mix(dusk_amb, overcast_amb, dist(gen)));
	} else if (mixtype < 0.66f) {
		Render::API::SetScreenClear(perturb1 + glm::mix(daytime_sun, overcast_sun, dist(gen)), true);
		Render::SetSunColor(perturb1 + glm::mix(daytime_sun, overcast_sun, dist(gen)));
		Render::SetAmbientColor(perturb2 + glm::mix(overcast_amb, overcast_amb, dist(gen)));
	} else {
		Render::API::SetScreenClear(perturb1 + glm::mix(dusk_sun, daytime_sun, dist(gen)), true);
		Render::SetSunColor(perturb1 + glm::mix(dusk_sun, daytime_sun, dist(gen)));
		Render::SetAmbientColor(perturb2 + glm::mix(dusk_amb, daytime_amb, dist(gen)));
	}
}

static void setup_camera() {
	Entity* target = Entity::Find(Segmentable::GetLoadableID());
	
	if (!target) return;
	
	static std::random_device rd;
    static std::mt19937 gen(rd());
    static std::uniform_real_distribution<float> dist(0.0f, 1.0f);

	// find a random offset from the target entity
	vec3 direction = {dist(gen), dist(gen), dist(gen)};
	direction = direction - 0.5f;
	if (glm::length(direction) < 0.01f) return;
	direction = 4.0f + dist(gen) * 20.0f * glm::normalize(direction);
	
	// setup the view to look at said entity
	vec3 campos = target->GetLocation() + direction;
	quat camrot = glm::quatLookAt(-glm::normalize(direction), DIRECTION_UP);
	
	// check if anything is in the way so that it might not be seen
	auto res = Render::AABB::FindNearestFromRay(campos, glm::normalize(camrot * DIRECTION_FORWARD), -1);
	
	// this is rather inelegant, but should work against getting us stuck in
	// an infinte loop
	static int recurse_depth = 0;
	if (!res.data) {
		if (recurse_depth > 15) {recurse_depth = 0; return;}
		recurse_depth++;
		setup_camera();
		return;
	}

	RenderComponent* comp = (RenderComponent*)res.data;

	if (comp->GetParent() != target) {
		if (recurse_depth > 15) {recurse_depth = 0; return;}
		recurse_depth++;
		setup_camera();
		return;
	}
	
	// add a small offset so that the entity is not centered
	vec3 offset = {dist(gen), dist(gen), dist(gen)};
	offset = offset - 0.5f;
	
	recurse_depth = 0;
	
	camrot = camrot * quat(offset);
	
	Render::SetViewPosition(campos);
	Render::SetViewRotation(camrot);
}

void SynthScenario::Setup() {
	auto cell = WorldCell::Make(worldcell);
	
	// it'd be better if we could query LOADED_FROM_DISK flag, but as that's
	// not possible rn, we'll use entity count as a proxy
	if (!cell->GetEntityCount()) {
		cell->LoadFromDisk();
	}	
	cell->Load();

	UI::SetWindowSize(256, 256);
	
	Render::SetSunDirection(glm::normalize(vec3(2.0f, 3.0f, 1.0f)));
	
	// dusk sorta color
	Render::SetSunColor(0.4f * Render::COLOR_WHITE + 0.2f * Render::COLOR_YELLOW);
	Render::SetAmbientColor(0.1f * Render::COLOR_WHITE + 0.1f * Render::COLOR_CYAN);
	
	// overcast
	Render::SetSunColor(0.6f * Render::COLOR_WHITE + 0.2f * Render::COLOR_YELLOW);
	Render::SetAmbientColor(0.1f * Render::COLOR_WHITE + 0.1f * Render::COLOR_CYAN);
	
	// daytime
	Render::SetSunColor(0.9f * Render::COLOR_WHITE + 0.2f * Render::COLOR_RED);
	Render::SetAmbientColor(0.1f * Render::COLOR_WHITE + 0.1f * Render::COLOR_CYAN);
	
	static name_t bind_cell;
	bind_cell = worldcell;
	UI::BindKeyboardKey(UI::KEY_P, [](){
		static bool saved = false;
		static bool as_segment = false;
		
		if (!saved) {
			reset_scene(bind_cell, false, false);
			saved = true;
			return;
		}
		
		save_image(as_segment);
		
		as_segment = !as_segment;
		reset_scene(bind_cell, false, as_segment);
		
		if (!as_segment) {
			setup_lighting();
			setup_camera();
		}
	});
	
	static bool* capture = &this->auto_capture;
	UI::BindKeyboardKey(UI::KEY_O, [](){
		*capture = !*capture;
	});
}

void SynthScenario::Teardown() {
	WorldCell::Find(worldcell)->Unload();
}

void SynthScenario::Update() {
	static int updates = 0;
	updates++;
	if (updates < 120 || updates % 8 != 0) return;
	if (!auto_capture) return;
	
	static bool saved = false;
	static bool as_segment = false;
		
	if (!saved) {
		reset_scene(worldcell, false, false);
		saved = true;
		return;
	}
	
	save_image(as_segment);
	
	as_segment = !as_segment;
	reset_scene(worldcell, false, as_segment);
	
	if (!as_segment) {
		setup_lighting();
		setup_camera();
	}
}