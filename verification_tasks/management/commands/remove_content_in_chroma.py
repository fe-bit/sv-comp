from django.core.management.base import BaseCommand
from verification_tasks.embedding.config import get_test_collection, get_train_collection, get_codet5p_embedder_collection, get_codet5p_embedder_collection_temp
from verification_tasks.embedding.helpers import transfer_entries


class Command(BaseCommand):
    help = "Remove document content from existing entries"

    def handle(self, *args, **options):
        print("Starting Cleanup Chroma DB...")
        target_collection = get_codet5p_embedder_collection()
        source_collection = get_codet5p_embedder_collection_temp()
        print("Transferring entries from source to target collection...")
        transfer_entries(source_collection=source_collection, target_collection=target_collection)
        print("Transfer completed.")
        # Fetch all entries with their ids, documents, embeddings, metadatas
        # entries = main_collection.get()

        # for batch in range(0, len(entries["ids"]), 1000):
        #     batch_ids = entries["ids"][batch:batch + 1000]
        #     batch_entries = main_collection.get(ids=batch_ids, include=["embeddings", "metadatas"])
            
        #     batch_embeddings = batch_entries["embeddings"]
        #     batch_metadatas = batch_entries["metadatas"]
        #     batch_ids = batch_entries["ids"]

        #     # Upsert back with empty documents to remove content but keep embeddings + metadata
        #     main_collection.update(
        #         documents=None,
        #         embeddings=batch_embeddings,
        #         metadatas=batch_metadatas,
        #         ids=batch_ids
        #     )
        #     self.stdout.write(self.style.SUCCESS(f"Cleared document content for {len(batch_ids)} entries"))

        # self.stdout.write(self.style.SUCCESS(f"Cleared document content for {len(entries["ids"])} entries"))
