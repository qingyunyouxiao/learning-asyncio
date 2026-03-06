#!/usr/bin/env python3

class Person:
    def __init__(self, name: str, age: int):
        if age < 0:
            age = 0
        self._name = name
        self._age = age
    
    def get_name(self) -> str:
        return self._name
    
    def get_age(self) -> int:
        return self._age

def main():
    person = Person("Alice", 30)
    print("Name:", person.get_name())
    print("Age:", person.get_age())

if __name__ == "__main__":
    main()