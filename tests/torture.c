/*
 * SPSC queue randomized torture tests.
 */
#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>
#include <inttypes.h>
#include <sys/types.h>
#include <unistd.h>
#include <pthread.h>

#include "spsc_queue.h"

#define D(x)
#define RANDOM_OBJ(s, x) random_fill(s, (&x), sizeof (x))

#define MAX_CAPACITY (1 * 1024)

struct torture_state {
	spsc_queue *tx_q;
	spsc_queue *rx_q;

	size_t tx_capacity;
	size_t rx_capacity;

	uint64_t tx_num;
	uint64_t rx_num;

	pthread_t loopback_worker;

	bool has_rx_worker;
	pthread_t rx_worker;
	unsigned int seed;
	volatile bool done;
};

static void random_fill(unsigned int *seedp, void *buf, size_t len) {
	unsigned char *d = buf;
	unsigned int i;

	for (i = 0; i < len; i++) {
		d[i] = rand_r(seedp);
	}
}

void hexdump(const char *prefix, const void *buf, size_t len)
{
	const unsigned char *u8 = buf;
	size_t i;

	if (prefix)
		printf("%s @ %p len=%u:\n", prefix, buf, (unsigned int) len);
	for (i = 0; i < len; i++) {
		if ((i % 16) == 0)
			printf("%u: ", (unsigned int) i);
		printf("%x ", u8[i]);
		if (((i + 1) % 16) == 0)
			putchar('\n');
	}
	putchar('\n');
}

spsc_queue *torture_open(const char *prefix, size_t capacity) {
	char name[] = "queue-XXXXYYYY.XXXXYYYY.";
	spsc_queue *q;
	uint64_t pid;
	int r;

	pid = getpid();
	r = snprintf(name, sizeof name, "queue-%s-%" PRIx64, prefix, pid);
	assert(r > 0);
	q = spsc_open(name, capacity);
	return q;
}

void torture_close(spsc_queue *q) {
	spsc_remove_shmfile(q->name);
	spsc_close(q);
}

void torture_ping(struct torture_state *ts) {
	uint8_t txbuf[SPSC_QUEUE_MAX_PACKET_SIZE * 2];
	uint8_t rxbuf[SPSC_QUEUE_MAX_PACKET_SIZE * 2];
	unsigned int shift;
	size_t len;
	bool r;

	// Randomize the entire txbuf, including shift area.
	RANDOM_OBJ(&ts->seed, txbuf);
	RANDOM_OBJ(&ts->seed, shift);
	shift %= SPSC_QUEUE_MAX_PACKET_SIZE;
	shift = 0;

	RANDOM_OBJ(&ts->seed, len);
	if (len < 0) {
		len = -len;
	}
	len %= SPSC_QUEUE_MAX_PACKET_SIZE;
	if (len == 0) {
		len = 1;
	}

	if (ts->has_rx_worker) {
		if (len < sizeof ts->tx_num) {
			len = sizeof ts->tx_num;
		}

		memcpy(txbuf + shift, &ts->tx_num, sizeof ts->tx_num);
		ts->tx_num++;
		D(hexdump("txbuf", txbuf + shift, len));
	}

	assert(len > 0);
	assert(len <= SPSC_QUEUE_MAX_PACKET_SIZE);

	do {
		r = spsc_send(ts->tx_q, txbuf + shift, len);
	} while (!r);

	if (ts->has_rx_worker) {
		return;
	}

	do {
		r = spsc_recv(ts->rx_q, rxbuf, len);
	} while (!r);
	assert(r);

	r = memcmp(rxbuf, txbuf + shift, len);
	if (r) {
		hexdump("txbuf", txbuf + shift, len);
		hexdump("rxbuf", rxbuf, len);
		assert(r == 0);
	}
}

void *torture_rx_worker(void *arg)
{
	uint8_t buf[SPSC_QUEUE_MAX_PACKET_SIZE];
	struct torture_state *ts = arg;
	spsc_queue *rx_q;
	uint64_t tx_num;
	int r;

	rx_q = torture_open("rx", ts->rx_capacity);
	while (!ts->done) {
		do {
			r = spsc_recv(rx_q, buf, SPSC_QUEUE_MAX_PACKET_SIZE);
			if (ts->done) {
				goto done;
			}
		} while (!r);
		assert(r);

		memcpy(&tx_num, buf, sizeof tx_num);

		if (tx_num != ts->rx_num) {
			printf("tx=%" PRIx64 " pkt=%" PRIx64 " rx=%" PRIx64 "\n",
				ts->tx_num, tx_num, ts->rx_num);
			hexdump("bad-buf", buf, SPSC_QUEUE_MAX_PACKET_SIZE);
			assert(0);
		}
		ts->rx_num++;
	}

done:
	torture_close(rx_q);
	return NULL;
}

void *torture_loopback_worker(void *arg)
{
	struct torture_state *ts = arg;
	uint8_t buf[SPSC_QUEUE_MAX_PACKET_SIZE];
	spsc_queue *tx_q;
	spsc_queue *rx_q;
	int r;

	tx_q = torture_open("tx", ts->tx_capacity);
	rx_q = torture_open("rx", ts->rx_capacity);

	while (!ts->done) {
		r = spsc_recv(tx_q, buf, SPSC_QUEUE_MAX_PACKET_SIZE);
		if (r) {
			do {
				D(hexdump("route buf", buf, SPSC_QUEUE_MAX_PACKET_SIZE));
				r = spsc_send(rx_q, buf, SPSC_QUEUE_MAX_PACKET_SIZE);
				if (ts->done) {
					goto done;
				}
			} while (!r);
		}
	}

done:
	torture_close(tx_q);
	torture_close(rx_q);
	return NULL;
}

void torture_launch_rx_worker(struct torture_state *ts) {
	int r;

	ts->has_rx_worker = true;
	r = pthread_create(&ts->rx_worker, NULL, torture_rx_worker, ts);
	assert(!r);
}

void torture_launch_loopback_worker(struct torture_state *ts) {
	int r;

	r = pthread_create(&ts->loopback_worker, NULL, torture_loopback_worker, ts);
	assert(!r);
}

size_t torture_rand_capacity(unsigned int *seedp) {
	size_t capacity;

	RANDOM_OBJ(seedp, capacity);
	capacity %= MAX_CAPACITY;
	if (capacity < 2) {
		capacity = 2;
	}

	return capacity;
}

void torture_test(struct torture_state *ts) {
	unsigned int i;
	unsigned int p;
	int r;

	printf("%s: ", __func__); fflush(NULL);
	for (i = 0; i < 2 * 1024; i++) {
		ts->done = false;

		ts->tx_capacity = torture_rand_capacity(&ts->seed);
		ts->rx_capacity = torture_rand_capacity(&ts->seed);

		ts->tx_q = torture_open("tx", ts->tx_capacity);
		ts->rx_q = torture_open("rx", ts->rx_capacity);

		assert(ts->tx_q);
		assert(ts->rx_q);

		ts->tx_num = 0;
		ts->rx_num = 0;

		D(printf("cap %zd %zd\n", ts->tx_capacity, ts->rx_capacity));
		torture_launch_loopback_worker(ts);

		torture_launch_rx_worker(ts);
		for (p = 0; p < (ts->tx_capacity * 2); p++) {
			torture_ping(ts);
		}

		ts->done = true;
		r = pthread_join(ts->loopback_worker, NULL);
		assert(r == 0);
		r = pthread_join(ts->rx_worker, NULL);
		assert(r == 0);

		torture_close(ts->tx_q);
		torture_close(ts->rx_q);

		if ((i & 16) == 0) {
			printf(".");
			fflush(NULL);
		}
	}
	printf("done\n");
}

void torture_test_open(struct torture_state *ts) {
	unsigned int i;
	int r;

	printf("%s: ", __func__); fflush(NULL);
	for (i = 0; i < 32 * 1024; i++) {
		ts->done = false;

		ts->tx_capacity = torture_rand_capacity(&ts->seed);
		ts->rx_capacity = torture_rand_capacity(&ts->seed);

		ts->tx_q = torture_open("tx", ts->tx_capacity);
		ts->rx_q = torture_open("rx", ts->rx_capacity);

		assert(ts->tx_q);
		assert(ts->rx_q);

		ts->tx_num = 0;
		ts->rx_num = 0;

		D(printf("cap %zd %zd\n", ts->tx_capacity, ts->rx_capacity));
		torture_launch_loopback_worker(ts);

		ts->has_rx_worker = false;
		// single ping.
		torture_ping(ts);

		ts->done = true;
		r = pthread_join(ts->loopback_worker, NULL);
		assert(r == 0);

		torture_close(ts->tx_q);
		torture_close(ts->rx_q);

		if ((i & 63) == 0) {
			printf(".");
			fflush(NULL);
		}
	}
	printf("done\n");

}

void torture_test_mapsize(struct torture_state *ts) {
	int c;

	printf("%s: ", __func__); fflush(NULL);
	for (c = 2; c < 1 * 1024 * 1024; c++) {
		size_t mapsize;
		int c2;

		mapsize = spsc_mapsize(c);
		c2 = spsc_capacity(mapsize);
		assert(c == c2);

		if ((c & 1023) == 0) {
			printf(".");
			fflush(NULL);
		}
	}
	printf("done\n");
}

int main(int argc, char *argv[]) {
	struct torture_state ts = {0};
	unsigned long runs = 1;

	if (argc > 1) {
		runs = strtoul(argv[1], NULL, 0);
	}

	torture_test_mapsize(&ts);

	while (runs--) {
		torture_test_open(&ts);
		torture_test(&ts);
	}

	printf("PASS\n");
	return EXIT_SUCCESS;
}
