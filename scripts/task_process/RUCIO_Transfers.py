#!/usr/bin/python

from ASO.Rucio.Rucio import main
import logging

if __name__ == "__main__":
    main_logger = logging.getLogger("main")
    try:
        # cProfile.run('main()')
        main_logger.debug("executing main()")
        main()
    except Exception as ex:
        print("error during main loop %s", ex)
        main_logger.exception("error during main loop")
    main_logger.info("transfer_inject.py exiting")
