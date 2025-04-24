API_VERSION = 'API_v1.0'
MOD_NAME = 'Draggable'

try:
    import events, ui, utils, dataHub, constants, battle, callbacks
except:
    pass

from EntityController import EntityController

CC = constants.UiComponents

def logInfo(*args):
    data = [str(i) for i in args]
    utils.logInfo( '[{}] {}'.format(MOD_NAME, ', '.join(data)) )

def logError(*args):
    data = [str(i) for i in args]
    utils.logError( '[{}] {}'.format(MOD_NAME, ', '.join(data)) )


START_DRAGGING  = 'action.modStartDragging'
STOP_DRAGGING   = 'action.modStopDragging'


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
        topLeftX, topLeftY = self.getTopLeft()
        minX, minY = bounds.getTopLeft()
        maxX, maxY = bounds.getBottomRight()

        pivotOffsetX = self.pivotX * self.width
        pivotOffsetY = self.pivotY * self.height

        clampedX = max(minX + pivotOffsetX, min(self.x, maxX - (self.width - pivotOffsetX)))
        clampedY = max(minY + pivotOffsetY, min(self.y, maxY - (self.height - pivotOffsetY)))

        self.x = clampedX
        self.y = clampedY


class Draggable(object):
    def __init__(self):
        self.stageWidth = None
        self.stageHeight = None
        self.stageScale = None
        self.screenRect = None
        self.elementRect = None
        self.dragOffset = None
        self._screenBoundsOffset = None
        self.isDragging = None
        self.__stage = None
        self.__dragEntity = None

        self._addEvents()
        logInfo('Initialized')

    def _addEvents(self, *args):
        stageEntity = dataHub.getSingleEntity('stage')
        if stageEntity:
            stage = stageEntity[CC.stage]
            stage.evStageSizeChanged.add(self.onStageSizeUpdate)
            self.__stage = stage
            self.onStageSizeUpdate()
            events.onSFMEvent(self.onSFMEvent)
        else:
            logError('Stage entity was not found.')

    def onSFMEvent(self, eventName, eventData):
        if eventName == START_DRAGGING:
            if self.isDragging:
                logError('Something is still being dragged!', self.__dragEntity._componentKey)
                self.stopDragging()
            elementName = eventData.get('elementName', None)
            elementBounds = eventData.get('elementBounds', None)
            elementPosition = eventData.get('elementPosition', None)
            screenBoundsOffset = eventData.get('screenBoundsOffset', None)
            dragOffset = eventData.get('dragOffset', None)
            if elementName and elementPosition and elementBounds and dragOffset:
                self.startDragging(elementName, elementPosition, elementBounds, screenBoundsOffset, dragOffset)
            else:
                logError('Draggable arguments are missing', elementName, elementBounds, elementPosition)

        elif eventName == STOP_DRAGGING:
            if not self.isDragging:
                logError('it wasnt even started')
            else:
                self.stopDragging()

    def startDragging(self, elementName, elementPosition, elementBounds, screenBoundsOffset, dragOffset):
        logInfo('Start dragging')
        dragEntity = EntityController(elementName)
        dragEntity.createEntity()
        self.__dragEntity = dragEntity
        self.dragOffset = dragOffset
        self._screenBoundsOffset = screenBoundsOffset
        self.screenRect = self.__createScreenRect()
        pivotX, pivotY = self.__calculatePivot(elementPosition, elementBounds)
        self.elementRect = Rectangle(elementPosition[0], elementPosition[1], elementBounds[2], elementBounds[3], pivotX, pivotY)

        events.onMouseEvent(self.onMouseEvent)
        self.isDragging = True

    def __calculatePivot(self, elementPosition, elementBounds):
        pivotX = (elementPosition[0] - elementBounds[0]) / elementBounds[2]
        pivotY = (elementPosition[1] - elementBounds[1]) / elementBounds[3]
        return (pivotX, pivotY)

    def __createScreenRect(self):
        bounds = self._screenBoundsOffset
        left    = bounds.get('left', 0)
        top     = bounds.get('top', 0)
        right   = bounds.get('right', 0)
        bottom  = bounds.get('bottom', 0)
        stage   = self.__stage
        w = stage.width - left - right
        h = stage.height - top - bottom
        return Rectangle(x=left, y=top, width=w, height=h)

    def stopDragging(self, *args):
        self.isDragging = False
        events.cancel(self.onMouseEvent)

        self._screenBoundsOffset = None
        self.screenRect = None
        self.elementRect = None

        self.__dragEntity.removeEntity()
        self.__dragEntity = None
        logInfo('Stop dragging')

    def onMouseEvent(self, mouseEvent):
        if self.isDragging:
            relPos = mouseEvent.cursorPosition # guaranteed to be in screen
            mouseX = (relPos[0] + 1) * 0.5 * self.stageWidth
            mouseY = (1 - relPos[1]) * 0.5 * self.stageHeight
            element = self.elementRect
            element.x, element.y = mouseX - self.dragOffset[0], mouseY - self.dragOffset[1]
            element.clampWithin(self.screenRect)
            self.__dragEntity.updateEntity({'dragPosX': element.x, 'dragPosY': element.y})

    def onStageSizeUpdate(self, *args):
        self.stageWidth = self.__stage.width
        self.stageHeight = self.__stage.height
        self.stageScale = self.__stage.scale
        if self.screenRect and self._screenBoundsOffset:
            self.screenRect = self.__createScreenRect()


draggable = Draggable()