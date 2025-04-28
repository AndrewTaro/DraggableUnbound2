API_VERSION = 'API_v1.0'
MOD_NAME = 'Draggable'

try:
    import events, ui, utils, dataHub, constants, battle, callbacks
except:
    pass

from EntityController import EntityController

CC = constants.UiComponents
DEFAULT_POSITION = (100, 100)

def logInfo(*args):
    data = [str(i) for i in args]
    utils.logInfo( '[{}] {}'.format(MOD_NAME, ', '.join(data)) )

def logError(*args):
    data = [str(i) for i in args]
    utils.logError( '[{}] {}'.format(MOD_NAME, ', '.join(data)) )


class DragEvents(object):
    ADD_DRAGGABLE       = 'action.modAddDraggable'
    REMOVE_DRAGGABLE    = 'action.modRemoveDraggable'
    START_DRAGGING      = 'action.modStartDragging'
    STOP_DRAGGING       = 'action.modStopDragging'


class Rectangle(object):
    def __init__(self, x, y, width, height, pivotX=0.0, pivotY=0.0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.pivotX = pivotX
        self.pivotY = pivotY

    def getTopLeft(self):
        return (
            self.x - self.width * self.pivotX,
            self.y - self.height * self.pivotY
        )

    def getBottomRight(self):
        topLeftX, topLeftY = self.getTopLeft()
        return (
            topLeftX + self.width,
            topLeftY + self.height
        )

    def clampWithin(self, bounds):
        minX, minY = bounds.getTopLeft()
        maxX, maxY = bounds.getBottomRight()

        pivotOffsetX = self.pivotX * self.width
        pivotOffsetY = self.pivotY * self.height

        clampedX = max(minX + pivotOffsetX, min(self.x, maxX - (self.width - pivotOffsetX)))
        clampedY = max(minY + pivotOffsetY, min(self.y, maxY - (self.height - pivotOffsetY)))

        self.x = clampedX
        self.y = clampedY


class Draggable(object):
    def __init__(self, elementName, defaultPosition):
        self.elementName = elementName
        self.screenRect = None
        self.elementRect = None
        self.dragOffset = None
        self.__screenBoundsOffset = None
        self.isDragging = None
        self.__stage = None
        self.defaultPosition = defaultPosition

        dragEntity = EntityController(elementName)
        dragEntity.createEntity(self.getSavedPosition())
        self.__dragEntity = dragEntity        

        self._addEvents()
        logInfo('Initialized')

    def _addEvents(self, *args):
        stageEntity = dataHub.getSingleEntity('stage')
        if stageEntity:
            stage = stageEntity[CC.stage]
            self.__stage = stage
            self.onStageSizeUpdate()
            stage.evStageSizeChanged.add(self.onStageSizeUpdate)
        else:
            logError('Stage entity was not found.')

    def getSavedPosition(self, *args):
        x =  ui.getUserPrefs('chatBoxWidth', self.elementName + '_positionX', self.defaultPosition.get('positionX', DEFAULT_POSITION[0]))
        y =  ui.getUserPrefs('chatBoxWidth', self.elementName + '_positionY', self.defaultPosition.get('positionY', DEFAULT_POSITION[1]))
        return {'dragPosX': x, 'dragPosY': y}

    def startDragging(self, data):
        # Origin
        #   ○--------------------
        #   |                    |
        #   |          Pivot     |
        #   |  Offset    ○       |
        #   |    ○               |
        #    --------------------
        #
        if self.isDragging:
            logError('It is still being dragged!', self.elementName)
            self.stopDragging()

        elementBounds = data.get('elementBounds', None)
        elementPosition = data.get('elementPosition', None) # Pivot Point
        screenBoundsOffset = data.get('screenBoundsOffset', None)
        dragOffset = data.get('dragOffset', None) # Offset to Origin
        if elementPosition and elementBounds and dragOffset:
            logInfo('Start dragging')
            self.dragOffset = dragOffset
            self.__screenBoundsOffset = screenBoundsOffset
            self.screenRect = self.__createScreenRect()
            pivotX, pivotY = self.__calculatePivot(elementPosition, elementBounds)
            self.elementRect = Rectangle(elementPosition[0], elementPosition[1], elementBounds[2], elementBounds[3], pivotX, pivotY)

            events.onMouseEvent(self.onMouseEvent)
            self.isDragging = True
        else:
            logError('Draggable arguments are missing. name: {}, bounds: {}, pos: {}, offset'.format(self.elementName, elementBounds, elementPosition, dragOffset))

    def __calculatePivot(self, elementPosition, elementBounds):
        pivotX = (elementPosition[0] - elementBounds[0]) / elementBounds[2] # (pivotX - originX) / width
        pivotY = (elementPosition[1] - elementBounds[1]) / elementBounds[3] # (pivotY - originY) / height
        return (pivotX, pivotY)

    def __createScreenRect(self):
        bounds = self.__screenBoundsOffset
        left    = bounds.get('left', 0)
        top     = bounds.get('top', 0)
        right   = bounds.get('right', 0)
        bottom  = bounds.get('bottom', 0)
        w = self.stageWidth  - left - right
        h = self.stageHeight - top - bottom
        return Rectangle(x=left, y=top, width=w, height=h)

    def stopDragging(self, *args):
        if not self.isDragging:
            logError('Dragging has not started')
            return
        
        self.isDragging = False
        events.cancel(self.onMouseEvent)
        self.__dragEntity.updateEntity({'dragPosX': self.elementRect.x, 'dragPosY': self.elementRect.y, 'isDragging': False})
        logInfo('Stop dragging')

    def kill(self, *args):
        if self.isDragging:
            self.stopDragging()
        self.__stage.evStageSizeChanged.remove(self.onStageSizeUpdate)
        self.__stage = None
        self.__dragEntity.removeEntity()
        self.__dragEntity = None
        self.__screenBoundsOffset = None
        self.screenRect = None
        self.elementRect = None
        self.dragOffset = None
        self.defaultPosition = None
        self.isDragging = None

    def onMouseEvent(self, mouseEvent):
        if self.isDragging:
            relPos = mouseEvent.cursorPosition # guaranteed to be in screen
            mouseX = (relPos[0] + 1) * 0.5 * self.stageWidth
            mouseY = (1 - relPos[1]) * 0.5 * self.stageHeight
            element = self.elementRect
            element.x, element.y = mouseX - self.dragOffset[0], mouseY - self.dragOffset[1]
            element.clampWithin(self.screenRect)
            self.__dragEntity.updateEntity({'dragPosX': element.x, 'dragPosY': element.y, 'isDragging': True})

    def onStageSizeUpdate(self, *args):
        if self.screenRect and self.__screenBoundsOffset:
            self.screenRect = self.__createScreenRect()

    @property
    def stageWidth(self):
        return self.__stage.width
    
    @property
    def stageHeight(self):
        return self.__stage.height
    
    @property
    def stageScale(self):
        return self.__stage.scale



class DraggableManager(object):
    def __init__(self):
        self.__draggableMap = {}
        events.onSFMEvent(self.onSFMEvent)

    def addDraggable(self, data):
        elementName = data.get('elementName')
        if elementName not in self.__draggableMap:
            default = data.get('defaultPosition', DEFAULT_POSITION)
            self.__draggableMap[elementName] = Draggable(elementName, default)
            logInfo('Added draggable', elementName)

    def removeDraggable(self, data):
        elementName = data.get('elementName')
        if elementName in self.__draggableMap:
            d = self.__draggableMap.pop(elementName)
            d.kill()
            logInfo('Removed draggable', elementName)

    def startDragging(self, data):
        elementName = data.get('elementName')
        if elementName in self.__draggableMap:
            self.__draggableMap[elementName].startDragging(data)

    def stopDragging(self, data):
        elementName = data.get('elementName')
        if elementName in self.__draggableMap:
            self.__draggableMap[elementName].stopDragging(data)

    def onSFMEvent(self, eventName, eventData):
        if eventName == DragEvents.ADD_DRAGGABLE:
            self.addDraggable(eventData)
        elif eventName == DragEvents.REMOVE_DRAGGABLE:
            self.removeDraggable(eventData)
        elif eventName == DragEvents.START_DRAGGING:
            self.startDragging(eventData)
        elif eventName == DragEvents.STOP_DRAGGING:
            self.stopDragging(eventData)


gManager = DraggableManager()