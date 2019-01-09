import random
import math
import os
import json
import copy
from types import *

from colorama import init as coloramaInit
from colorama import Fore, Back, Style

from monster import Monster
from item import Item
from player import Player
from room import Room
from maps import Map
from door import Door
from utils import Utils

class Game:
    def __init__(self):
        self.initialize()
        
    def initialize(self):
        self.mode = "start"
        self.quit = False
        self.turn = 1
        self.nextLevel = 100
        self.level = 1
        self.map = None
        self.options = {
            "start": "<L>oad, <N>ew",
            "combat": "<A>ttack, <D>efend, <R>un",
            "peace": "<R>est, <C>ontinue, <I>nventory, <S>ave",
            "gameOver": "<R>estart, <Q>uit",
            "inventory": "<E>quip, <C>lose",
            "map": lambda : self.map.getOptions() if self.map else ""
        }
        self.resolver = {
            "start": self.startResolve,
            "combat": self.combatResolve,
            "peace": self.peaceResolve,
            "gameOver": self.gameOverResolve,
            "inventory": self.inventoryResolve,
            "map": self.mapResolve
        }
        self.display = {
            "start": self.startDisplay,
            "combat": self.combatDisplay,
            "peace": self.peaceDisplay,
            "gameOver": self.gameOverDisplay,
            "inventory": self.inventoryDisplay,
            "map": self.mapDisplay
        }
        self.clearResolution()
        self.nextTurn()

### NUMBER METHODS ###

    def rollDie(self, size):
        return random.randint(1, size)
    
    def incrementDungeonLevel(self):
        self.level += 1
        self.nextLevel += (100 * self.level)
        self.map.dungeonLevel = self.level

    def incrementTurn(self, numTurns = 1):
        self.turn += numTurns
        if self.turn >= self.nextLevel:
            self.incrementDungeonLevel()
            self.addResolution(f"{Fore.RED}The dungeon seems more dangerous...")
    
### PRINTING METHODS ###

    def printRoll(self, roll, target):
        self.addResolution(f"[{roll} vs {target}]")
        
    def printStats(self):
        displayFunc = self.display[self.mode]
        displayFunc()

    def clearResolution(self):
        self.resolution = []

    def addResolution(self, text):
        self.resolution.append(text)

    def printResolution(self):
        if len(self.resolution) > 0:
            print("\n" + "\n".join(self.resolution))

### DISPLAY METHODS ###

    def startDisplay(self):
        print(f"{Style.BRIGHT}Welcome To The Dungeon!\n")

    def combatDisplay(self):
        print(f"{Style.BRIGHT}Dungeon Level {self.level} - Turn {self.turn}\n")
        self.player.printStats()
        print("")
        self.monster.printStats()

    def peaceDisplay(self):
        print(f"{Style.BRIGHT}Dungeon Level {self.level} - Turn {self.turn}\n")
        self.player.printStats()
        print("")
        room = self.map.getCurrentRoom()
        room.printStats(self.map.getCurrentDoors())

    def inventoryDisplay(self):
        self.player.printInventory()

    def mapDisplay(self):
        self.map.printFloor(self.turn)

    def gameOverDisplay(self):
        self.player.printHistory()

    def printOptions(self):
        options = self.options[self.mode]
        if type(options) is LambdaType:
            options = options()
        print(f"\n{Style.BRIGHT}{options}")

### COMBAT METHODS ###

    def playerAttack(self):
        atkRoll = self.rollDie(20) + self.player.atk
        
        monsterDefense = self.monster.ac
            
        if atkRoll >= monsterDefense:
            damRoll = self.rollDie(self.player.dam)
            self.addResolution(f"{Fore.GREEN}You {self.player.getAtkVerb()} the {self.monster.name} for {damRoll}")
            damage = self.monster.damage(damRoll, self.player.atkType)
            if damage < damRoll:
                self.addResolution(f"{Fore.MAGENTA}Your weapon is not very effective.")
            if damage > damRoll:
                self.addResolution(f"{Fore.CYAN}Your weapon is very effective.")
            self.player.incrementHistory("dmg_done", damage)
        else:
            self.addResolution(f"{Fore.WHITE}You miss!")
        # self.printRoll(atkRoll, monsterDefense)
                
    def monsterAttack(self, playerDefending):
        atkRoll = self.rollDie(20) + self.monster.atk
        
        playerDefense = self.player.ac
        if playerDefending:
            playerDefense = playerDefense * 2

        if atkRoll >= playerDefense:
            damRoll = self.rollDie(self.monster.dam)
            self.addResolution(f"{Fore.RED}The {self.monster.name} {self.monster.getAtkVerb()} you for {Style.BRIGHT}{damRoll}")
            self.player.damage(damRoll, self.monster.atk_type)
            self.player.incrementHistory("dmg_taken", damRoll)
        else:
            self.addResolution(f"{Fore.WHITE}The {self.monster.name} misses!")
        # self.printRoll(atkRoll, playerDefense)

    def getReward(self, level):
        xp = self.monster.level * 100
        gp = self.monster.level * self.rollDie(10)
        self.player.xp += xp
        self.player.gp += gp
        self.addResolution(f"\n{Fore.YELLOW}You got {xp} XP and {gp} GP")
        
        levelUp = self.player.checkLevelUp()
        if levelUp:
            if self.level < self.player.level:
                self.incrementDungeonLevel()
            self.addResolution(f"{Fore.YELLOW}You gained a level!")

        item = Item(self.monster.level)
        if item.kind:
            self.player.addItem(item)
            self.addResolution(f"{Fore.YELLOW}You found: {item.displayName}")

    def deathCheck(self):
        if self.player.hp <= 0:
            self.addResolution(f"{Fore.RED}{Style.BRIGHT}You die!")
            self.player.killedBy(self.monster, self.level)
            self.mode = "gameOver"

### RESOLUTION METHODS ###

    def mapResolve(self, action):
        if action == "B":
            self.mode = "peace"
        elif action in ["N", "S", "E", "W", "U", "D"]:
            direction = action.lower()
            for key, door in self.map.getCurrentDoors():
                if key[0] == direction and door.exists:
                    if direction == "u" and self.map.playerPosition[0] == 0:
                        print(f"{Fore.MAGENTA}{Style.BRIGHT}Are you sure you want to exit the dungeon? <Y>es or <N>o")
                        choice = input()
                        if choice.lower() == "y":
                            self.mode = "gameOver"
                            self.player.setEpitaph("Escaped the dungeon!")
                            return True
                    else:
                        self.map.movePlayer(direction)
                        door.useDoor()
                        if 'traveling' in self.player.abilities:
                            travelRoll = self.rollDie(10)
                            if travelRoll > self.player.getAbilityLevel('traveling'):
                                self.incrementTurn()
                        else:
                            self.incrementTurn()
                        monster = self.map.getCurrentRoom().monster
                        if monster != None:
                            self.monster = monster
                            self.mode = "combat"
        else:
            return False
        return True

    def startResolve(self, action):
        if action == "L":            
            load = self.loadSave()
        elif action == "N":
            print("Choose a name:")
            name = input()
            self.player = Player(name)
            self.map = Map()
        else:
            return False
        self.mode = "peace"
        return True

    def combatResolve(self, action):
        if action == "A":            
            self.playerAttack()
                
            if self.monster.hp <= 0:
                self.addResolution(f"The {self.monster.name} dies!")
                self.map.getCurrentRoom().removeMonster()
                self.player.incrementHistory("kills")
                if self.player.hp <= self.player.maxHp * .25:
                    self.player.incrementHistory("risky_win")
                self.getReward(self.monster.level)
                self.monster = None
                self.mode = "peace"
            else:
                self.monsterAttack(False)  
                self.deathCheck()
            self.incrementTurn()
        elif action == "D":
            self.addResolution("You defend yourself!")

            self.monsterAttack(True)
            self.deathCheck()
            self.incrementTurn()
        elif action == "R":
            self.player.incrementHistory("run_away")
            exits = self.map.getCurrentDoors()
            escaped = False
            while not escaped:
                door = random.choice(exits)
                if (door[1].used):
                    self.map.movePlayer(door[0])
                    escaped = True
            self.mode = "peace"
            if 'running' in self.player.abilities:
                self.incrementTurn(10 - self.player.getAbilityLevel('running'))
                self.addResolution(f"{Fore.GREEN}You run away very quickly!")
            else:
                self.incrementTurn(10)
                self.addResolution("You run away!")
        else:
            return False
        return True

    def peaceResolve(self, action):
        if action == "C":
            self.mode = "map"
        elif action == "R":
            self.addResolution("You take some time to recover...")
            restFactor = math.sqrt(self.player.level)
            if 'regeneration' in self.player.abilities:
                restFactor -= 0.2 * self.player.getAbilityLevel('regeneration')
                self.addResolution(f"{Fore.GREEN}You heal quickly...")
            timeToRest = math.floor((self.player.maxHp - self.player.hp) * restFactor)
            self.player.heal()
            self.player.incrementHistory("rest")
            self.incrementTurn(timeToRest)
        elif action == "I":
            self.mode = "inventory"
        elif action == "S":
            self.createSave()
            print("<C>ontinue or <Q>uit?")
            choice = input()
            if len(choice) > 0 and choice[0].upper() == "Q":
                self.quit = True
        else:
            return False
        return True

    def gameOverResolve(self, action):
        if action == "R":
            print("restart")
            self.initialize()
        if action == "Q":
            self.quit = True
        return True

    def inventoryResolve(self, action):
        if action == "E":
            print("Which item do you wish to equip?")
            complete = False
            while not complete:
                itemNum = input()
                if itemNum == "":
                    complete = True
                else:
                    try:
                        i = int(itemNum) - 1
                        try:
                            item = self.player.items[i]
                            self.player.equipItem(i)
                            complete = True
                        except IndexError:
                            print("Invalid item number")
                    except ValueError:
                        #Handle the exception
                        print("Please enter an integer")
        if action == "C":
            self.mode = "peace"
        return True

### LIFECYCLE METHODS ###

    def takeInput(self):
        self.printOptions()
        resolved = False
        self.clearResolution()
        action = input()
        if len(action) > 0:
            action = action[0].upper()
            self.resolver[self.mode](action)
        
    def nextTurn(self):
        clear()
        self.printStats()
        self.printResolution()
        self.takeInput()

    def createSave(self):
        saveObj = {
            "player": dict(copy.deepcopy(self.player).__dict__),
            "map": dict(copy.deepcopy(self.map).__dict__),
            "game": {
                "turn": self.turn,
                "nextLevel": self.nextLevel,
                "level": self.level
            }
        }

        # make player items serializable
        saveObj["items"] = []
        for item in saveObj["player"]["items"]:
            saveObj["items"].append(item.__dict__)
        del saveObj["player"]["items"]

        # make map rooms serializable
        saveObj["map"]["rooms"] = {}
        saveObj["map"]["monsters"] = {}
        saveObj["map"]["doors"] = {
            "ns": {},
            "ew": {}
        }
        saveObj["map"]["stairs"] = {}

        for f, floor in enumerate(saveObj["map"]["floors"]):
            for r in range(self.map.width):
                for c in range(self.map.width):
                    saveKey = f"{f}-{r}-{c}"
                    roomDict = floor["rooms"][(r,c)].__dict__
                    monster = roomDict["monster"]
                    saveObj["map"]["monsters"][saveKey] = monster.__dict__ if monster != None else None
                    del roomDict["monster"]
                    saveObj["map"]["rooms"][saveKey] = roomDict
                    try: 
                        ns = floor["doors"]["ns"][(r,c)].__dict__
                        saveObj["map"]["doors"]["ns"][saveKey] = ns
                    except KeyError:
                        pass
                    try:
                        ew = floor["doors"]["ew"][(r,c)].__dict__
                        saveObj["map"]["doors"]["ew"][saveKey] = ew
                    except KeyError:
                        pass
                    try:
                        stairs = floor["stairs"][(r,c)].__dict__
                        saveObj["map"]["stairs"][saveKey] = stairs
                    except KeyError:
                        pass

        del saveObj["map"]["floors"]

        # save the file
        with open('save.txt', 'w') as outfile:  
                json.dump(saveObj, outfile)

    def loadSave(self):
        with open('save.txt') as json_file:  
            load = json.load(json_file)
            self.player = Player(load["player"]["name"], load["player"])
            self.player.loadItems(load["items"])
            for i in load["game"]:
                setattr(self, i, load["game"][i])
            self.map = Map(load["map"]["numFloors"], load["map"]["width"], load["map"])


clear=lambda: os.system('cls' if os.name == 'nt' else 'clear')
coloramaInit(autoreset=True)
game = Game()
while not game.quit:
    game.nextTurn()
clear()
