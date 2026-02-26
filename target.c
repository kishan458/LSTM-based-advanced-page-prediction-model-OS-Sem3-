#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <unistd.h>
#include <string.h>
#include <fcntl.h>
#include <time.h>

#define PAGE_SIZE 4096
#define TOTAL_PAGES 1000

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: ./target [1-4]\n");
        return 1;
    }
    srand(time(NULL));
    int type = atoi(argv[1]);
    char shm_name[64];
    sprintf(shm_name, "/page_shm_%d", getpid());

    int shm_fd = shm_open(shm_name, O_CREAT | O_RDWR, 0666);
    ftruncate(shm_fd, sizeof(int));
    int *shared_page = mmap(NULL, sizeof(int), PROT_READ|PROT_WRITE, MAP_SHARED, shm_fd, 0);

    size_t size = 100 * 1024 * 1024;
    char *base = mmap(NULL, size, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS|MAP_POPULATE, -1, 0);
    memset(base, 0, size);

    printf("\033[1;32m[SYSTEM] Process Started\033[0m\n");
    printf("PID:    %d\n", getpid());
    printf("OFFSET: %p\n", base);
    printf("SHM:    %s\n", shm_name);
    printf("--------------------------\n");

    int current_page = type * 100;
    int history[10]; // To facilitate "locality"
    int step = 0;

    while (1) {
        int stride;
        // Every 5th step, revisit a recently used page (Locality for LRU)
        if (step % 5 == 0 && step > 10) {
            current_page = history[rand() % 10];
        } else {
            stride = (type == 1) ? ((current_page % 3 == 0) ? 1 : 3) :
                     (type == 2) ? ((current_page % 3 == 0) ? 2 : 5) :
                     (type == 3) ? ((current_page % 3 == 0) ? 4 : 10) :
                                   ((current_page % 3 == 0) ? 1 : 2);
            current_page = (current_page + stride) % TOTAL_PAGES;
        }

        history[step % 10] = current_page;
        volatile char *ptr = base + current_page * PAGE_SIZE;
        *ptr = 'A'; 

        *shared_page = current_page;
        step++;
        usleep(400000); // Faster updates for smoother UI
    }
}