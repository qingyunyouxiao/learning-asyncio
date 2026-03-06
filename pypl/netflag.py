#!/usr/bin/env python3

FlagUp = 1 << 0
FlagBroadcast = 1 << 1
FlagLoopback = 1 << 2
FlagPointToPoint = 1 << 3
FlagMulticast = 1 << 4

def is_up(v):
    return (v & FlagUp) == FlagUp

def turn_down(v):
    return v & (~FlagUp)

def set_broadcast(v):
    return v | FlagBroadcast

def is_cast(v):
    return (v & (FlagBroadcast | FlagMulticast)) != 0

def main():
    v = FlagMulticast | FlagUp
    print(f"{bin(v)[2:]}, {is_up(v)}")
    
    v = turn_down(v)
    print(f"{bin(v)[2:]}, {is_up(v)}")
    
    v = set_broadcast(v)
    print(f"{bin(v)[2:]}, {is_up(v)}")
    
    print(f"{bin(v)[2:]}, {is_cast(v)}")

if __name__ == "__main__":
    main()