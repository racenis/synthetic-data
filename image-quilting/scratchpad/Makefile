CC = gcc
#CFLAGS = -Wall -Wextra -O2 -I../library
CFLAGS = -I../library
LDFLAGS =

# Source files
SRCS = main.c ../library/quilt.c ../library/image.c ../library/patch.c

# Object files (replace .c with .o, keep path)
OBJS = $(SRCS:.c=.o)

# Target executable
TARGET = scratchpad

# Default target
all: $(TARGET)

# Link
$(TARGET): $(OBJS)
	$(CC) $(OBJS) -o $@ $(LDFLAGS)

# Compile rules
%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

# Clean up
clean:
	rm -f $(OBJS) $(TARGET)

.PHONY: all clean