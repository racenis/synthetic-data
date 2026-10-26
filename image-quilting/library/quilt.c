#include "quilt.h"

#include "patch.h"

void quilt_quilt(quilt_image_t* source, quilt_image_t* image) {
	for (int y = 0; y < image->height; y += 16)
	for (int x = 0; x < image->width; x += 16) {
		quilt_patch_t patch;
		
		int flags = 0;
		if (x != 0) flags |= PATCH_USE_LEFT;
		if (y != 0) flags |= PATCH_USE_TOP;
		
		quilt_patch_pick(source, image, &patch, 16, 16, x, y, flags);
		
		for (int py = 0; py < 16; py++)
		for (int px = 0; px < 16; px++) {
			const int r = quilt_image_sample_r(source, patch.x + px, patch.y + py);
			const int g = quilt_image_sample_g(source, patch.x + px, patch.y + py);
			const int b = quilt_image_sample_b(source, patch.x + px, patch.y + py);

			quilt_image_write_r(image, x + px, y + py, r);
			quilt_image_write_g(image, x + px, y + py, g);
			quilt_image_write_b(image, x + px, y + py, b);
		}
	}
}