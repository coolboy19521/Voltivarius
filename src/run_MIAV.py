from MIAV import miav
from gpiozero import Button
from rclpy import init, spin, shutdown

but = Button(23)

def main():
    init()
    node = miav()
    print('Running')
    try:
        spin(node)
    #except Exception as e:
    #    print(e)
    finally:
        node.destroy_node()
        shutdown()

if __name__ == '__main__':
    but.wait_for_press()
    main()
