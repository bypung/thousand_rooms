import random

from colored import fore, back, style

from .item_list import ItemList
from .utils import Utils

class Item:
    def __init__(self, level, data = None, force = []):
        self.isEgo = False
        self.equipped = False
        self.kind = ''

        if level > 0:
            self.level = level
        
        if data:
            for i in data:
                setattr(self, i, data[i])
        else:
            info = self.getItem(level)
            while len(force) > 0 and (not info or info["kind"] not in force):
                info = self.getItem(level // 2)
            if info != None:
                for i in info:
                    setattr(self, i, info[i])
                
                if self.effect:
                    self.displayName = f"{self.name} of {self.effect.title()}"
                elif self.ability:
                    self.displayName = f"{self.name} of {self.ability.title()}"
                else:
                    self.displayName = self.name

                # improved items
                if self.kind != "usable":
                    if self.kind == "ring":
                        self.level = (level + 1) // 2
                    levelDiff = level - self.level
                    if levelDiff > 0:
                        try:
                            descriptor = ItemList.descriptors[self.kind][levelDiff // 2]
                        except KeyError:
                            pass
                        try:
                            descriptor = ItemList.descriptors[self.kind][self.type][levelDiff // 2]
                        except KeyError:
                            pass
                        except TypeError:
                            pass
                        self.displayName = f"{descriptor} {self.displayName}"
                        self.level += levelDiff
                        if self.atk:
                            self.atk += levelDiff // 2
                        if self.ac:
                            self.ac += levelDiff // 2

                if self.kind in ["weapon", "armor"]:
                    egoChance = random.randint(1,100)
                    if egoChance <= level:
                        self.generateEgo()

    def generateEgo(self):
        self.isEgo = True

        if self.kind == "weapon":
            ego = random.choice(ItemList.weaponEgo)
            self.atk += ego["bonus"]
        else:
            ego = random.choice(ItemList.armorEgo)
            self.ac += ego["bonus"]

        self.displayName += f" of {ego['name']}"
        for key in ego["attributes"]:
            setattr(self, key, ego["attributes"][key])

    def getAbilityLevel(self):

        if self.ability:
            return (self.level + 1) // 2
        else:
            return 0

    @staticmethod
    def getItem(level):
        itemRoll = random.randint(level, 100)
        kind = "none"
        
        if itemRoll < 80:
            return None
        if itemRoll < 88:
            kind = "usable"
        elif itemRoll < 93:
            kind = "weapon"
        elif itemRoll < 98:
            kind = "armor"
        else:
            kind = "ring"
    
        if kind in ["usable", "ring"]:
            items = [item for item in ItemList.items if item["kind"] == kind and item["level"] <= level] 
        else:
            items = [item for item in ItemList.items if item["kind"] == kind and item["level"] <= level and item["level"] > level - 8] 
        return random.choice(items) if len(items) else None

    @staticmethod
    def getOptions(source, options):
        page = options["currPage"]
        pageSize = options["pageSize"]
        filterValue = options["filter"]
        mode = options["mode"]
        message = options["message"]
        if mode in ["buy", "sell"]:
            message = f"{fore.YELLOW}GP: {options['gp']}  {style.RESET}{message}"
        sourceType = type(source).__name__
        actions = []
        if sourceType == "Player":
            if mode == "combat":
                actions = ["<U>se"]  
            elif mode == "sell":
                actions = ["<B>uy", "<S>ell"]  
            else:
                actions = ["<E>quip", "<U>se"]
        elif sourceType == "Store":
            actions = ["<B>uy", "<S>ell"]
        
        filteredItems = source.items if filterValue == "all" else list(filter(lambda i: i.kind == filterValue, source.items))
        totalItems = len(filteredItems)

        navigation = []
        if page > 0:
            navigation += ["<P>rev Page"]
        if (page + 1) * pageSize < totalItems:
            navigation += ["<N>ext Page"]

        leave = ["<L>eave"] if sourceType == "Store" else ["<C>lose"]
        filterOption = [] if mode == "combat" else ["<F>ilter"]
        out = actions + navigation + filterOption + leave
        out = message + f"{style.RESET}\n" + ", ".join(out) + style.RESET
        options["message"] = ""
        return out

    @staticmethod
    def getItemPrice(item, valueFactor):
        price = item.level * valueFactor
        if item.kind == "usable":
            price = price * 2
        if item.isEgo:
            price = price * 3
        return price

    @staticmethod
    def getItemBonus(item):
        out = ""
        if item.atk:
            out += f"{item.atk}"
        if item.ac:
            out += f"{item.ac}"
        if item.ability and not "resist_" in item.ability:
            ability = item.getAbilityLevel()
            out += f"{ability}" if out == "" else f"({ability})"
        return out

    @staticmethod
    def getItemAbility(item):
        out = ""
        abbreviations = {
            "regeneration": "regen",
            "resist_fire": "res. fire",
            "resist_cold": "res. cold",
            "resist_acid": "res. acid",
            "resist_electric": "res. electric"
        }
        if item.ability:
            try:
                out += abbreviations[item.ability]
            except KeyError:
                out += item.ability
        return out

    @staticmethod
    def printInventory(source, options):
        page = options["currPage"]
        pageSize = options["pageSize"]
        filterValue = options["filter"]
        sourceType = type(source).__name__
 
        filterHeader = "" if filterValue == "all" else f" ({filterValue.title()})"
        if sourceType == "Player":
            print(f"{fore.CYAN}{style.BOLD}{source.name}'s Inventory{filterHeader}{style.RESET}")
            valueFactor = options["sellFactor"]
        elif sourceType == "Store":
            print(f"{fore.MAGENTA}{style.BOLD}Store Inventory{filterHeader}{style.RESET}")
            valueFactor = options["buyFactor"]

        filteredItems = source.items if filterValue == "all" else list(filter(lambda i: i.kind == filterValue, source.items))

        startIndex = pageSize * page
        s = slice(startIndex, startIndex + pageSize)
        pageItems = filteredItems[s]
        
        itemLines = []
        for i, item in enumerate(pageItems, 1):
            line = {
                "Name": f"{startIndex + i}) {item.displayName}",
                "Bonus": item.getItemBonus(item),
                "Type": f"{item.type}",
                "Ability": item.getItemAbility(item),
                "Value": f"{Item.getItemPrice(item, valueFactor)}"
            }
            if sourceType == "Player":
                line["_color"] = fore.GREEN if item.equipped else style.RESET

            itemLines.append(line)

        Utils.printTable(["   Name", "Bonus", "Type", "Ability", "Value"], itemLines, [40, 7, 8, 12, 8])

    @staticmethod
    def getFilteredItem(source, options, index):
        filterValue = options["filter"]
 
        filteredItems = source.items if filterValue == "all" else list(filter(lambda i: i.kind == filterValue, source.items))

        try:
            return filteredItems[index]
        except IndexError:
            return None