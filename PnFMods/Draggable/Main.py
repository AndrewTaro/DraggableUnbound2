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

class Draggable(object):
    def __init__(self):
        self.stageWidth = None
        self.stageHeight = None
        self.stageScale = None
        self.x = None
        self.y = None
        self.offsetX = None
        self.offsetY = None
        self.maxBoundsX = None
        self.maxBoundsY = None
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
            elementSize = eventData.get('elementSize', None)
            dragOffsets = eventData.get('dragOffsets', None)
            if elementName and dragOffsets and elementSize:
                self.startDragging(elementName, elementSize, dragOffsets)
            else:
                logError('Draggable arguments are missing', elementName, elementSize, dragOffsets)

        elif eventName == STOP_DRAGGING:
            if not self.isDragging:
                logError('it wasnt even started')
            else:
                self.stopDragging()

    def startDragging(self, elementName, elementSize, dragOffsets):
        logInfo('Start dragging')
        dragEntity = EntityController(elementName)
        dragEntity.createEntity()
        self.__dragEntity = dragEntity
        self.offsetX = dragOffsets[0]
        self.offsetY = dragOffsets[1]
        self.maxBoundsX = self.stageWidth  - elementSize[0]
        self.maxBoundsY = self.stageHeight - elementSize[1]
        events.onMouseEvent(self.onMouseEvent)
        self.isDragging = True

    def stopDragging(self, *args):
        self.isDragging = False
        events.cancel(self.onMouseEvent)
        self.maxBoundsX = None
        self.maxBoundsY = None
        self.offsetX = None
        self.offsetY = None
        self.__dragEntity.removeEntity()
        self.__dragEntity = None
        logInfo('Stop dragging')

    def onMouseEvent(self, mouseEvent):
        if self.isDragging:
            relPos = mouseEvent.cursorPosition # guaranteed to be in screen
            mouseX = (relPos[0] + 1) * 0.5 * self.stageWidth
            mouseY = (1 - relPos[1]) * 0.5 * self.stageHeight
            dragX = min(max(mouseX - self.offsetX, 0), self.maxBoundsX)
            dragY = min(max(mouseY - self.offsetY, 0), self.maxBoundsY)
            self.__dragEntity.updateEntity({'dragPosX': dragX, 'dragPosY': dragY})

    def onStageSizeUpdate(self, *args):
        if self.__stage:
            self.stageScale  = self.__stage.scale
            self.stageWidth  = self.__stage.width
            self.stageHeight = self.__stage.height


draggable = Draggable()