class Variable:
    TEMP_PREFIX = 'webmap_temp_'
    
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)

    def __init__(self, tag, prop, value):
        self.tag = tag
        self.prop = prop
        self.value = value

    def __repr__(self) -> str:
        return f"{self.formatVariableName(self.tag, self.prop)}={self.value}"
    
    def getVariableName(self) -> str:
        return self.formatVariableName(self.tag, self.prop)
    
    def fromVariableNameAndValue(name, value):
        possibleVars = re.findall(r'\[.*?\]', name)

        if possibleVars is None or possibleVars.__len__() == 0:
            return None
        
        prop = possibleVars.pop()[1:-1] if possibleVars.__len__() > 0 else None

        if prop is None:
            return None

        tag = name.replace(f'[{prop}]', '')

        return Variable(tag, prop, value)

    @staticmethod
    def formatVariableName(tag, property) -> str:
        return f'{tag}[{property}]'
    
    @staticmethod
    def formatTempVariableName(tag, property) -> str:
        return f'{Variable.TEMP_PREFIX}{tag}[{property}]'
    
    def fromDict(dict):
        return Variable(dict['tag'], dict['prop'], dict['value'])
