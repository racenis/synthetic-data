#include "drone.h"

#include <framework/worldcell.h>
#include <framework/ui.h>
#include <framework/core.h>
#include <framework/event.h>
#include <framework/file.h>

#include <platform/image.h>
#include <platform/api.h>

#include <render/api.h>

#include <thread>

static DroneScenario* bound_scenario = nullptr;

DroneScenario::DroneScenario(name_t worldcell, bool autopilot) : worldcell(worldcell), autopilot(autopilot) {
	
}

void DroneScenario::Setup() {
	auto cell = WorldCell::Make(worldcell);
	
	// it'd be better if we could query LOADED_FROM_DISK flag, but as that's
	// not possible rn, we'll use entity count as a proxy
	if (!cell->GetEntityCount()) {
		cell->LoadFromDisk();
	}
	
	UI::SetWindowSize(224, 224);
	
	cell->Load();
	
	Render::API::SetScreenClear(0.4f * Render::COLOR_WHITE + 0.2f * Render::COLOR_YELLOW, true);
	Render::SetSunColor(0.4f * Render::COLOR_WHITE + 0.2f * Render::COLOR_YELLOW);
	Render::SetAmbientColor(0.1f * Render::COLOR_WHITE + 0.1f * Render::COLOR_CYAN);
	
	bound_scenario = this;
	
	Event::AddListener(Event::KEYPRESS, [](Event& event){
		switch (event.subtype) {
			case UI::KEY_ACTION_FORWARD:
				bound_scenario->ApplyControl(DroneControl::THRUST, 0.08f); break;
			case UI::KEY_ACTION_BACKWARD:
				bound_scenario->ApplyControl(DroneControl::THRUST, -0.02f); break;
			case UI::KEY_ACTION_STRAFE_LEFT:
				bound_scenario->ApplyControl(DroneControl::ROLL, 0.02f); break;
			case UI::KEY_ACTION_STRAFE_RIGHT:
				bound_scenario->ApplyControl(DroneControl::ROLL, -0.02f); break;
			case UI::KEY_ACTION_UP:
				bound_scenario->ApplyControl(DroneControl::PITCH, -0.02f); break;
			case UI::KEY_ACTION_DOWN:
				bound_scenario->ApplyControl(DroneControl::PITCH, 0.02f); break;
		}
	});
}

void DroneScenario::Teardown() {
	WorldCell::Find(worldcell)->Unload();
	
	if (bound_scenario == this) bound_scenario = nullptr;
}

void DroneScenario::ApplyControl(DroneControl control, float amount) {
	switch (control) {
		case DroneControl::THRUST:{
			velocity += (GetRotation() * DIRECTION_FORWARD) * amount;
		}
			return;
		case DroneControl::PITCH:
			pitch += amount; return;
		case DroneControl::ROLL:
			roll += amount; return;
	}
}

quat DroneScenario::GetRotation() {
	return quat(vec3(0.0f, yaw, 0.0f)) * quat(vec3(pitch, 0.0f, 0.0f)) * quat(vec3(0.0f, 0.0f, roll));
}

void DroneScenario::Update() {
	float linear_velocity = glm::length(vec3(velocity.x, 0.0f, velocity.z));
	vec3 lift = 0.05f * linear_velocity * (GetRotation() * DIRECTION_UP);
	
	position += -DIRECTION_UP * (/*9.8f*/ 4.0f * GetDeltaTime());
	position += 0.4f * lift;
	position += velocity * GetDeltaTime();
	
	yaw += GetDeltaTime() * linear_velocity * roll * 0.5f;
	
	velocity *= 0.99f;
	
	static auto mixrot = GetRotation();
	mixrot = glm::mix(GetRotation(), mixrot, 0.9f);
	
	if (position.y < 0.0f) position.y = 0.0f, velocity.y = 0.0f;
	
	Render::SetViewPosition(position);
	Render::SetViewRotation(mixrot);
	
	DrawBoxes();
}

static void save_buffer(char* buffer, char* filename, int w, int h) {
	Platform::SaveImageToDisk(filename, w, h, buffer);
	
	free(buffer);
	free(filename);
}

static void write_out(int index) {
	auto screen_width = UI::GetScreenWidth();
	auto screen_height = UI::GetScreenHeight();
	char* buffer = (char*)malloc(screen_width * screen_height * 3);
	
	char* file_name = (char*)malloc(200);
	snprintf(file_name, 200, "predict-%i.png", index);
	
	Render::API::GetScreen(buffer, screen_width, screen_height);
	
	std::thread(save_buffer, buffer, file_name, screen_width, screen_height).detach();
}

void DroneScenario::DrawBoxes() {
	for (auto box : boxes) {
		if (box.conf < 0.7f) continue;
		
		auto color = box.conf < 0.9f ? Render::COLOR_YELLOW : Render::COLOR_GREEN;
		
		Render::AddText(box.x, box.y, "+", color);
		Render::AddText(box.x, box.h, "+", color);
		Render::AddText(box.w, box.y, "+", color);
		Render::AddText(box.w, box.h, "+", color);
		
		char confidence_text[100];
		snprintf(confidence_text, 100, "%.2f", box.conf);
		
		Render::AddText(box.x + 16, box.y + 16, confidence_text, color);
	}
	
	static int checks = 0;
	if (++checks < 4) return;
	checks = 0;
	
	// we should probably use a pipe instead of spamming the disk with
	// incrementally numbered .pngs and .txts, but i'm feeling frisky today
	static int last_index = 0;
	static bool wrote_out = false;
	
	if (!wrote_out) {
		write_out(last_index);
		wrote_out = true;
	}
	
	char file_name[200];
	snprintf(file_name, 200, "result-%i.txt", last_index);
	
	File file(file_name, File::READ);
	if (!file.is_open()) return;
	
	boxes.clear();
	auto token = file.read_name();
	while (file.is_continue()) {
		if (token == "end") {
			Log("finished file!");
			break;
		}
		
		if (token == "box") {
			boxes.push_back(Box{file.read_int32(), file.read_int32(), file.read_int32(), file.read_int32(), file.read_float32()});
		} else {
			Log("unrecognized token {} in file {}", token, file_name);
			return;
		}
		
		token = file.read_name();
	}
	
	last_index++;
	write_out(last_index);
}