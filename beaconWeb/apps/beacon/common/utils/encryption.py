#simple bit relocation hash. not super secure but good enough to prevent users from guessing random beacon_invite ids
#simple_int_hash(n): hashed value
#simple_int_hash(simple_int_hash(n)): original value


def simple_int_hash(n):
    return ((0x0000FFFF & n)<<16) + ((0xFFFF0000 & n)>>16)


