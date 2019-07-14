import kivy.uix.boxlayout
import kivy.uix.textinput
import kivy.uix.label
import kivy.uix.button
import kivy
from kivy.app import App
import keras

class SimpleApp(App):

    def build(self):

        self.textInput = kivy.uix.textinput.TextInput()
        self.label = kivy.uix.label.Label(text="Your Message.")
        self.button = kivy.uix.button.Button(text="Click Me.")

        message = self.textInput.text + ' with Keras version ' + keras.__version__

        self.button.bind(on_press=self.displayMessage(message))
        self.boxLayout = kivy.uix.boxlayout.BoxLayout(orientation="vertical")
        self.boxLayout.add_widget(self.textInput)
        self.boxLayout.add_widget(self.label)
        self.boxLayout.add_widget(self.button)

        return self.boxLayout

    def displayMessage(self, message):
        self.label.text = message


if __name__ == "__main__":
    simpleApp = SimpleApp()
    simpleApp.run()


