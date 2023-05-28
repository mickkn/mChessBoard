


def parser():

    """
    Parser function to get all the arguments
    """

    # Construct the argument parse and return the arguments
    args = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    args.add_argument(
        "-p",
        "--port",
        type=int,
        default=80,
        help="listening port",
    )
    args.add_argument("-d", "--debug", action="store_true", help="debug printout")


    print("\n" + str(args.parse_args()) + "\n")

    return args.parse_args()


def signal_handler(sig, frame):

    """! @brief    Exit function"""

    print(" SIGINT or CTRL-C detected. Exiting gracefully")
    sys.exit(0)


async_mode = None
app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()



    

if __name__ == "__main__":

    """! @brief    Main function"""

    # CTRL+C handler
    signal(SIGINT, signal_handler)

    # Parse arguments
    args = parser()

    if args.debug:
        socketio.run(app=app, host='0.0.0.0', port=args.port, debug=True)
    else:
        socketio.run(app=app, host='0.0.0.0', port=args.port, debug=False)
    