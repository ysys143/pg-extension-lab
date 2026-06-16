#include <assert.h>
#include <stddef.h>

static int
candidate_score(int value, int bias)
{
    return value + bias;
}

int
main(void)
{
    assert(candidate_score(10, 5) == 15);
    assert(candidate_score(-1, 1) == 0);
    return 0;
}

