all: ITGManager$(SUFFIX) DummyManager$(SUFFIX)


OBJS = ../common/thread.o common.o stats.o DummyManager.o
OBJS2=../common/thread.o common.o stats.o ITGManager.o

DummyManager$(SUFFIX): ../libITG/ITGapi.h $(OBJS)
ifeq ($(BUILD_ENV),WIN32_MINGW)
	@ echo [ LD ]  $@ ^<- $(OBJS)
else
	@ printf "[ LD ]\t$@ <- $(OBJS)\n"
endif
	@ $(CXX) $(CXXFLAGS) $(OBJS) -L$(BIN) -lITG -o $@ $(LDFLAGS)
	@ $(CP) $@ $(BIN)

ITGManager$(SUFFIX): ../libITG/ITGapi.h $(OBJS2)
ifeq ($(BUILD_ENV),WIN32_MINGW)
	@ echo [ LD ]  $@ ^<- $(OBJS2)
else
	@ printf "[ LD ]\t$@ <- $(OBJS2)\n"
endif
	@ $(CXX) $(CXXFLAGS) $(OBJS2) -L$(BIN) -lITG -o $@ $(LDFLAGS)
	@ $(CP) $@ $(BIN)

clean:
ifeq ($(BUILD_ENV),WIN32_MINGW)
	@- $(RM) *.o DummyManager$(SUFFIX) $(BIN)\DummyManager$(SUFFIX)
	@- $(RM) *.o ITGManager$(SUFFIX) $(BIN)\ITGManager$(SUFFIX)
else
	@ $(RM) *.o DummyManager$(SUFFIX) $(BIN)/DummyManager$(SUFFIX)
	@ $(RM) *.o ITGManager$(SUFFIX) $(BIN)/ITGManager$(SUFFIX)
endif

#---------------
include ../common.mk
#---------------
