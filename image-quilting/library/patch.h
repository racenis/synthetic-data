#ifndef PATCH_H
#define PATCH_H

#include "image.h"

typedef struct {
	int width;
	int height;
	
	int x;
	int y;
	
	quilt_image_t* source;
} quilt_patch_t;

void quilt_patch_from_coords(quilt_image_t* source, quilt_patch_t* patch, int w, int h, int x, int y);
void quilt_patch_pick(quilt_image_t* source, quilt_image_t* image, quilt_patch_t* patch, int w, int h, int x, int y, int flags);

enum {
	PATCH_USE_TOP = 1,
	PATCH_USE_RIGHT = 2,
	PATCH_USE_BOTTOM = 4,
	PATCH_USE_LEFT = 8,
	
	// maybe mirror left-to-right and mirror top-to-bottom?
};

#endif // PATCH_H