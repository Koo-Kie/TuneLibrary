from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap
import sys, ressource_rc, threading, queue
from io import BytesIO
from functions import *

class RatingDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Rate out of 100 Stars")
        self.setFixedSize(200, 100)  # Set window size

        layout = QVBoxLayout()

        self.label = QLabel("Rate out of 100 stars:")
        layout.addWidget(self.label)

        self.spin_box = QSpinBox()
        self.spin_box.setRange(0, 100)
        self.spin_box.setValue(50)
        layout.addWidget(self.spin_box)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)

    def getRating(self):
        return self.spin_box.value()

class Ui(QMainWindow):
    def __init__(self):
        # Init
        super(Ui, self).__init__()
        uic.loadUi('gui.ui', self)
        self.show()
        self.pages_wrapper.setCurrentIndex(0)
        # output_queue = queue.Queue()
        # thread = threading.Thread(target=make_api_call, args=(data,))
        # thread.start()

        # Connectors
        self.menu_button.clicked.connect(lambda: self.pages_wrapper.setCurrentIndex(0))
        self.search_button.clicked.connect(lambda: self.pages_wrapper.setCurrentIndex(1))
        self.playlist_button.clicked.connect(lambda: self.pages_wrapper.setCurrentIndex(2))

        self.add_to_button.currentIndexChanged.connect(self.addMusicToPlaylist)
        
        self.create_playlist_button.clicked.connect(self.create_playlist)
        self.delete_playlist_button.clicked.connect(self.delete_playlist)
        self.rating_playlist_button.clicked.connect(self.rate_music)
        self.preview_button_2.clicked.connect(lambda: self.preview_music('playlist'))
        self.pause_button_2.clicked.connect(player.pause)
        self.stop_button_2.clicked.connect(player.stop)
        self.volume_slider_2.valueChanged.connect(lambda: player.set_volume(self.volume_slider.value()))

        self.music_search_button.clicked.connect(self.search_function)
        self.preview_button.clicked.connect(lambda: self.preview_music(self.music_search_result_list.currentItem()))
        self.pause_button.clicked.connect(player.pause)
        self.stop_button.clicked.connect(player.stop)
        self.volume_slider.valueChanged.connect(lambda: player.set_volume(self.volume_slider.value()))

        clear_cache()
        
        featured = get_featured_songs()
        discover = get_discover_songs()

        self.title_label1.setText(discover[0].get('name'))
        self.title_label2.setText(discover[1].get('name'))
        self.title_label3.setText(discover[2].get('name'))
        self.title_label4.setText(discover[3].get('name'))

        self.author_label_1.setText(discover[0].get('artist'))
        self.author_label_2.setText(discover[1].get('artist'))
        self.author_label_3.setText(discover[2].get('artist'))
        self.author_label_4.setText(discover[3].get('artist'))

        self.popularity_label_1.setText("🔥" + str(discover[0].get('popularity')))
        self.popularity_label_2.setText("🔥" + str(discover[1].get('popularity')))
        self.popularity_label_3.setText("🔥" + str(discover[2].get('popularity')))
        self.popularity_label_4.setText("🔥" + str(discover[3].get('popularity')))

        temp_image_path = create_temp_image(download_image(discover[0]["cover_url"]))
        self.featured_song_cover_1.setPixmap(QPixmap(temp_image_path))
        temp_image_path = create_temp_image(download_image(discover[1]["cover_url"]))
        self.featured_song_cover_2.setPixmap(QPixmap(temp_image_path))
        temp_image_path = create_temp_image(download_image(discover[2]["cover_url"]))
        self.featured_song_cover_3.setPixmap(QPixmap(temp_image_path))
        temp_image_path = create_temp_image(download_image(discover[3]["cover_url"]))
        self.featured_song_cover_4.setPixmap(QPixmap(temp_image_path))

        self.title_label_a.setText(featured[0].get('name'))
        self.title_label_b.setText(featured[1].get('name'))
        self.title_label_c.setText(featured[2].get('name'))
        self.title_label_d.setText(featured[3].get('name'))

        self.author_label_a.setText(featured[0].get('artist'))
        self.author_label_b.setText(featured[1].get('artist'))
        self.author_label_c.setText(featured[2].get('artist'))
        self.author_label_d.setText(featured[3].get('artist'))

        self.popularity_label_a.setText("🔥" + str(featured[0].get('popularity')))
        self.popularity_label_b.setText("🔥" + str(featured[1].get('popularity')))
        self.popularity_label_c.setText("🔥" + str(featured[2].get('popularity')))
        self.popularity_label_d.setText("🔥" + str(featured[3].get('popularity')))

        temp_image_path = create_temp_image(download_image(featured[0]["cover_url"]))
        self.featured_song_cover_a.setPixmap(QPixmap(temp_image_path))
        temp_image_path = create_temp_image(download_image(featured[1]["cover_url"]))
        self.featured_song_cover_b.setPixmap(QPixmap(temp_image_path))
        temp_image_path = create_temp_image(download_image(featured[2]["cover_url"]))
        self.featured_song_cover_c.setPixmap(QPixmap(temp_image_path))
        temp_image_path = create_temp_image(download_image(featured[3]["cover_url"]))
        self.featured_song_cover_d.setPixmap(QPixmap(temp_image_path))


        self.output_queue = queue.Queue()  # Create a queue to receive results
        self.populatePlaylists()

        self.closeEvent = self.close_app

    def close_app(self, event):
        player.terminate()  # Signal thread to stop
        player.join()  # Wait for thread to finish
        event.accept() 

    def search_function(self):
        query = self.search_query_input.text()

        thread = threading.Thread(target=self._threaded_search, args=(query,))
        thread.start()

    def _threaded_search(self, query):
        result = search_music(query)  # Perform the search in the background thread
        self.output_queue.put(result)  # Put the result in the queue

    def update_results(self):
        while not self.output_queue.empty():
            self.result = self.output_queue.get()
            self.music_search_result_list.clear()

            for index, music in enumerate(self.result):
                item = QListWidgetItem(f"{music['name']} - {', '.join(artist for artist in music['artists'])} \n{music['duration']}")
                item.setData(Qt.UserRole, music['preview_url'])
                temp_image_path = create_temp_image(download_image(music["cover_url"]))
                self.result[index]["cover_url"] = temp_image_path
                
                if temp_image_path is not None:
                    icon = QIcon(temp_image_path)
                    item.setIcon(icon)
                else:
                    print("Image download failed or URL was not provided.")
                self.music_search_result_list.addItem(item)
                

    def preview_music(self, item):
        if item == 'playlist':
            selected_items = self.playlist_viewer.selectedItems()

            if not selected_items:
                print("No playlists selected.")
                return

            playlist_item = selected_items[0].parent()
            if playlist_item == None:
                return
            else:
                playlist_name = playlist_item.text(0).replace(' ', '_')
                id = selected_items[0].data(0, Qt.UserRole)

                connection = sqlite3.connect('playlists.db')
                cursor = connection.cursor()
                query = "SELECT * FROM {} WHERE id = ?".format(playlist_name)
                cursor.execute(query, (id,))
                result = cursor.fetchone()
                player.play_song(result[5])


        elif item:
            url = item.data(Qt.UserRole)
            if url == None:
                print('No preview available')
            else:
                player.play_song(url) 
                

    def timerEvent(self, event):
        self.update_results()


    def populatePlaylists(self):

        self.playlist_viewer.clear()
        self.add_to_button.clear()
        data = get_playlists_and_songs()
        self.add_to_button.addItem('Add to')

        for playlist, songs in data.items():
            playlist_item = QTreeWidgetItem(self.playlist_viewer, [playlist])
            self.add_to_button.addItem(playlist)
            for song in songs:
                try:
                    if song[6]:
                        song_item = QTreeWidgetItem(playlist_item, [song[1], song[2], song[3], f"{song[6]}⭐"])
                    else:
                        song_item = QTreeWidgetItem(playlist_item, [song[1], song[2], song[3]])
                    song_item.setData(0, Qt.UserRole, song[0])
               
                
                    # song_item.setText(1, song[2])
                    # song_item.setText(2, song[3])

                    if song[4] is not None:
                        pixmap = QPixmap()
                        pixmap.loadFromData(BytesIO(song[4]).read())
                        icon = QIcon(pixmap)
                        song_item.setIcon(0, icon)
                    else:
                        print("Image download failed or URL was not provided.")
                except:
                    pass
                
        
        for i in range(self.playlist_viewer.columnCount()):
            self.playlist_viewer.resizeColumnToContents(i)

    def addMusicToPlaylist(self):
        selected_music = self.music_search_result_list.currentItem()
        playlist = self.add_to_button.currentText().strip()
        self.add_to_button.setCurrentIndex(0)
        if selected_music and playlist not in ('Add to', ''):
            index = self.music_search_result_list.row(selected_music)
            print('entered', self.result[index])
            add_entry_to_playlist(playlist.replace(' ', '_'), (self.result[index]["name"], 
                                               ",".join(self.result[index]["artists"]),
                                               self.result[index]["duration"], 
                                               self.result[index]["cover_url"], 
                                               self.result[index].get("preview_url"))
                                               )
            self.populatePlaylists()

    def create_playlist(self):
        text, ok = QInputDialog.getText(self, "Create a new playlist", "Enter your playlist name:")
        if ok:
            create_playlist_table(text)
            self.populatePlaylists()
    
    def show_confirmation_dialog(self):
        dialog = QMessageBox()
        dialog.setWindowTitle("Are you sure?")
        dialog.setText("Are you sure you want to delete playlist?")
        dialog.setIcon(QMessageBox.Question)
        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dialog.setDefaultButton(QMessageBox.No)
        return dialog.exec()

    def delete_playlist(self):

        result = self.show_confirmation_dialog()
        if result == QMessageBox.Yes:
            print("User clicked Yes")

            selected_playlists = self.playlist_viewer.selectedItems()

            if not selected_playlists:
                print("No playlists selected.")
                return

            playlist_name = selected_playlists[0].text(0).replace(' ', '_')

            try:
                connection = sqlite3.connect('playlists.db')
                cursor = connection.cursor()

                drop_table_query = "DROP TABLE {}".format(sanitize_string(playlist_name))
                cursor.execute(drop_table_query)

                connection.commit()
                print(f"Playlist '{playlist_name}' deleted successfully.")
            except sqlite3.OperationalError as e:
                if "no such table" in str(e).lower():
                    print(f"Playlist '{playlist_name}' does not exist.")
                    print(selected_playlists[0].data(0, Qt.UserRole))
                    id = selected_playlists[0].data(0, Qt.UserRole)
                    music_name = selected_playlists[0].text(0)
                    try:
                        cursor = connection.cursor()
                        parent_name = selected_playlists[0].parent().text(0).replace(' ', '_')
                        delete_query = "DELETE FROM {} WHERE id = ?".format(parent_name)
                        cursor.execute(delete_query, (id,))

                        connection.commit()
                        print(f"Row with name '{music_name}' deleted successfully from table '{selected_playlists[0].parent().text(0)}'.")

                    except sqlite3.Error as e:
                        print(f"An error occurred: {e}")

                    finally:
                        connection.close()
                else:
                    print(f"An error occurred while deleting '{playlist_name}': {e}")
            finally:
                connection.close()

            self.populatePlaylists()

        else:
            print("User clicked No")

    def rate_music(self):
        dialog = RatingDialog()
        if dialog.exec_():
            rating = dialog.getRating()
            print("User rated:", rating, "out of 100 stars")
            

            selected_playlists = self.playlist_viewer.selectedItems()

            if not selected_playlists:
                print("No playlists selected.")
                return

            
            playlist = selected_playlists[0].parent().text(0).replace(' ', '_').lower()
            id = selected_playlists[0].data(0, Qt.UserRole)
            try:
                conn = sqlite3.connect('playlists.db')
                cursor = conn.cursor()
                print(rating)
                cursor.execute(f"UPDATE {playlist} SET rating = ?  WHERE id = ?", (rating, id))
                
                conn.commit()
                conn.close()
            except Exception as e:
                print(f'Error: {e}')

            self.populatePlaylists()

        else:
            print("User clicked No")



if __name__ == "__main__":
    player = MusicPlayer()
    player.start()

    app = QApplication(sys.argv)
    window = Ui()
    window.startTimer(500)
    window.show()
    sys.exit(app.exec())
