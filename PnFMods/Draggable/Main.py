API_VERSION = 'API_v1.0'
MOD_NAME = 'Draggable'

try:
    import events, ui, utils, dataHub, constants, battle, callbacks
except:
    pass

from EntityController import EntityController

CC = constants.UiComponents

COMPONENT_KEY = 'modTeamHP'

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
        self._stageWidth = None
        self._stageHeight = None
        self._stageScale = None
        self._x = None
        self._y = None
        self._offsetX = None
        self._offsetY = None
        self._maxBoundsX = None
        self._maxBoundsY = None
        self._isDragging = None
        self.__stage = None
        self._dragEntity = None

        self._addEvents()

    def _addEvents(self, *args):
        stageEntity = dataHub.getSingleEntity('stage')
        if stageEntity:
            stage = stageEntity[CC.stage]
            stage.evStageSizeChanged.add(self.onStageChange)
            self.__stage = stage
            self.onStageChange()
            events.onSFMEvent(self.onSFMEvent)
        else:
            logError('Stage entity was not found.')

    def onSFMEvent(self, eventName, eventData):
        if eventName == START_DRAGGING:
            if self._isDragging:
                logError('stop!')
                self.onStopDragging()
            elementName = eventData.get('elementName', 'modDraggable')
            dragOffsets = eventData.get('dragOffsets', (0,0))
            elementSize = eventData.get('elementSize', (40, 40))
            self.onStartDragging(elementName, dragOffsets, elementSize)

        elif eventName == STOP_DRAGGING:
            if not self._isDragging:
                logError('it wasnt even started')
            else:
                self.onStopDragging()

    def onStartDragging(self, elementName, dragOffsets, elementSize):
        logInfo('Start dragging')
        dragEntity = EntityController(elementName)
        dragEntity.createEntity()
        self._dragEntity = dragEntity
        self._offsetX = dragOffsets[0]
        self._offsetY = dragOffsets[1]
        self._maxBoundsX = self._stageWidth  - elementSize[0]
        self._maxBoundsY = self._stageHeight - elementSize[1]
        events.onMouseEvent(self.onMouseEvent)
        self._isDragging = True

    def onStopDragging(self, *args):
        self._isDragging = False
        events.cancel(self.onMouseEvent)
        self._maxBoundsX = None
        self._maxBoundsY = None
        self._offsetX = None
        self._offsetY = None
        self._dragEntity.removeEntity()
        self._dragEntity = None
        logInfo('Stop dragging')

    def onMouseEvent(self, mouseEvent):
        if self._isDragging:
            relPos = mouseEvent.cursorPosition # guaranteed to be in screen
            mouseX = (relPos[0] + 1) * 0.5 * self._stageWidth
            mouseY = (1 - relPos[1]) * 0.5 * self._stageHeight
            dragX = min(max(mouseX - self._offsetX, 0), self._maxBoundsX)
            dragY = min(max(mouseY - self._offsetY, 0), self._maxBoundsY)
            if self._dragEntity:
                self._dragEntity.updateEntity({'dragPosX': dragX, 'dragPosY': dragY})

    def onStageChange(self, *args):
        if self.__stage:
            self._stageScale  = self.__stage.scale
            self._stageWidth  = self.__stage.width
            self._stageHeight = self.__stage.height


draggable = Draggable()