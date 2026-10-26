#include "patch.h"

void quilt_patch_from_coords(quilt_image_t* source, quilt_patch_t* patch, int w, int h, int x, int y) {
	memset(patch, 0, sizeof(quilt_patch_t));
	
	patch->width = w;
	patch->height = h;
	
	patch->x = x;
	patch->y = y;
	
	patch->source = source;
}

void quilt_patch_pick(quilt_image_t* source, quilt_image_t* image, quilt_patch_t* patch, int w, int h, int x, int y, int flags) {
	// the original image quilting paper suggests using a 1/6 size border
	int border_w = w / 6 + 1;
	int border_h = h / 6 + 1;
	
	// TODO: if not PATCH_USE_XYZ is set, maybe choose a patch at random?
	
	// to make similarity comparison simpler, we'll first generate a mask to
	// determine which pixels in the patch should contribute to the similarity
	int mask_w = border_w + border_w + w;
	int mask_h = border_h + border_h + h;
	
	int mask_size = mask_w * mask_h;
	char* mask = malloc(mask_size);
	memset(mask, 0, mask_size);
	
	// first we'll initialize all of the pixels of the mask, while skipping over
	// the borders that we won't need to compare
	int x_start = flags & PATCH_USE_LEFT ? 0 : border_w;
	int x_end = flags & PATCH_USE_RIGHT ? mask_w : mask_w - border_w;
	
	int y_start = flags & PATCH_USE_TOP ? 0 : border_h;
	int y_end = flags & PATCH_USE_BOTTOM ? mask_h : mask_h - border_h;

	for (int y = y_start; y < y_end; y++)
	for (int x = x_start; x < x_end; x++) {
		const int offset = y * mask_w + x;
		mask[offset] = 1;
	}
	
	// then we cut out the middle of the patch, keeping only the borders
	for (int y = border_h; y < mask_h - border_h; y++)
	for (int x = border_w; x < mask_w - border_w; x++) {
		const int offset = y * mask_w + x;
		mask[offset] = 0;
	}
	
	// now we can iterate over the various candidate patches and find the best
	// candidates for the patch in the image
	int worst_score = INT_MAX;
	int worst_index = 0;
	int candidates_scores[16];
	int candidates_x[16];
	int candidates_y[16];
	for (int i = 0; i < 16; i++) {
		candidates_scores[i] = INT_MAX;
		candidates_x[i] = 0;
		candidates_y[i] = 0;
	}
	
	for (int candidate_y = 0; candidate_y < source->height; candidate_y += h)
	for (int candidate_x = 0; candidate_x < source->width; candidate_x += w) {
		const int source_x = candidate_x - border_w;
		const int source_y = candidate_y - border_h;
		const int image_x = x - border_w;
		const int image_y = y - border_h;
		
		int this_score = 0;
		
		for (int y = 0; y < mask_h; y++)
		for (int x = 0; x < mask_w; x++) {
			const int offset = y * mask_w + x;
			if (!mask[offset]) continue;
			
			const int s_r = quilt_image_sample_r(source, source_x + x, source_y + y);
			const int s_g = quilt_image_sample_g(source, source_x + x, source_y + y);
			const int s_b = quilt_image_sample_b(source, source_x + x, source_y + y);
			
			const int i_r = quilt_image_sample_r(image, image_x + x, image_y + y);
			const int i_g = quilt_image_sample_g(image, image_x + x, image_y + y);
			const int i_b = quilt_image_sample_b(image, image_x + x, image_y + y);
			
			this_score += (s_r - i_r) * (s_r - i_r);
			this_score += (s_g - i_g) * (s_g - i_g);
			this_score += (s_b - i_b) * (s_b - i_b);
			
			if (this_score > worst_score) goto give_up_on_this_candidate;
		}
	give_up_on_this_candidate:
		
		if (this_score > worst_score) continue;
		
		candidates_scores[worst_index] = this_score;
		candidates_x[worst_index] = candidate_x;
		candidates_y[worst_index] = candidate_y;
		
		worst_score = 0;
		for (int i = 0; i < 16; i++) {
			if (candidates_scores[i] < worst_score) continue;
			worst_score = candidates_scores[i];
			worst_index = i;
		}
	}
	
	free(mask);
	mask = NULL;
	
	// for now we'll just use a hash instead of an actual random function for
	// reproducibility during debugging
	static unsigned long hash = 5381;
	hash = ((hash << 5) + hash) + worst_score;
	
	const int selected_candidate = hash % 16;
	
	const int select_x = candidates_x[selected_candidate];
	const int select_y = candidates_y[selected_candidate];
	
	// okay, we're done here ;33
	quilt_patch_from_coords(source, patch, w, h, select_x, select_y);
}